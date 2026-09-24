#!/usr/bin/env python3
"""Supervisor — owns the QEMU process and its private QMP stdio channel.

One Supervisor per running env instance. The QMP pipe is stdin/stdout of
the spawned process: no socket, no monitor mixed on stdout, no other
reader/writer. `powerdown` is graceful first (QMP system_powerdown); a
deadline that expires never silently escalates to kill — force requires
the caller (EnvironmentManager) to have collected a new consent.

Daemon mode (`python cu_env_daemon.py --env-dir <dir>`) is the
long-lived owner: it spawns QEMU, negotiates QMP, then serves a per-user
AF_UNIX socket inside the env's private dir. Each connection is one
JSON-line request {command, arguments} -> one JSON-line response
{ok, return|error[, error_class]}. The daemon dies with QEMU (poll loop)
and kills QEMU on its own exit — no orphans by construction.
"""
import atexit
import json
import os
import socket
import sys
import time
from pathlib import Path

import cu_env
import cu_qmp


class Supervisor:
    """Wrap a spawned QEMU proc: negotiate QMP, expose typed ops."""

    def __init__(self, proc, deadline_s=10):
        self.proc = proc
        self.qmp = cu_qmp.QmpClient(proc.stdout, proc.stdin,
                                    deadline_s=deadline_s)

    def negotiate(self):
        """Consume greeting + qmp_capabilities. Raises QmpError on EOF,
        timeout or protocol violation — caller treats as failed start."""
        self.qmp.negotiate()

    def call(self, command, arguments=None):
        return self.qmp.call(command, arguments)

    def powerdown(self, timeout_s=15, force=False):
        """Graceful ACPI shutdown via QMP; force=True kills only after the
        caller re-consented. Timeout without force raises TimeoutError —
        a stuck guest is `unknown`, never silently killed."""
        try:
            self.qmp.call("system_powerdown")
        except cu_qmp.QmpError:
            pass  # channel dead — wait/kill path still applies
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                return
            time.sleep(0.1)
        if force:
            self.proc.kill()
            self.proc.wait(timeout=5)
            return
        raise TimeoutError("powerdown_timeout")


def _confined(env_dir, filename):
    """screendump writes on the HOST filesystem — the path a client asks
    for must resolve inside env_dir, no exceptions."""
    env_dir = Path(env_dir).resolve()
    p = Path(filename)
    if not p.is_absolute():
        p = env_dir / p
    rp = p.resolve()
    if os.path.commonpath([str(env_dir), str(rp)]) != str(env_dir):
        raise ValueError(f"escape:{filename}")
    return str(rp)


class Journal:
    """Request journal — dedup by request_id. completed -> cached
    response replay-free; accepted-but-never-completed (daemon died
    mid-call) -> request_uncertain, the op NEVER re-executes."""
    def __init__(self, path):
        self.path = Path(path)
        self._recs = {}
        try:
            for line in self.path.read_text("utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    self._recs[r["request_id"]] = {
                        "state": r["state"],
                        "response": r.get("response")}
        except FileNotFoundError:
            pass

    def _append(self, rid, state, command=None, response=None):
        rec = {"request_id": rid, "state": state, "command": command,
               "response": response}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def begin(self, rid, command):
        self._recs[rid] = {"state": "accepted", "response": None}
        self._append(rid, "accepted", command)

    def complete(self, rid, response):
        self._recs[rid] = {"state": "completed", "response": response}
        self._append(rid, "completed", response=response)

    def execute(self, rid, command, args, fn):
        if rid is None:
            return fn(command, args)  # no id -> no dedup possible
        rec = self._recs.get(rid)
        if rec is not None:
            if rec["state"] == "completed":
                return rec["response"]
            return {"ok": False, "error": "request_uncertain",
                    "request_id": rid}
        self.begin(rid, command)
        resp = fn(command, args)
        self.complete(rid, resp)
        return resp


_RELEASE_KEYS = ("shift", "shift_r", "ctrl", "ctrl_r",
                 "alt", "alt_r", "meta_l", "meta_r")
_RELEASE_BTNS = ("left", "right", "middle", "side", "extra")


def _release_events():
    """Up-events for every modifier/button — remote emergency_release."""
    return ([{"type": "key",
              "data": {"key": {"type": "qcode", "data": k},
                       "down": False}} for k in _RELEASE_KEYS]
            + [{"type": "btn", "data": {"button": b, "down": False}}
               for b in _RELEASE_BTNS])


def _handle(qmp, obj, env_dir, journal=None, guest=None):
    """One IPC request. command is already constrained by QmpClient's
    allowlist; screendump filenames get host-path confinement.
    guest-call ops bypass the journal — guest payloads (clipboard!)
    are untrusted content, never persisted."""
    cmd = obj.get("command")
    args = obj.get("arguments") or {}
    if cmd == "guest-call":
        if guest is None:
            return {"ok": False, "error": "guest_channel_unavailable"}
        method = args.get("method")
        if not isinstance(method, str):
            return {"ok": False, "error": "guest-call:method required"}
        try:
            return {"ok": True,
                    "return": guest.call(method,
                                         args.get("params") or {})}
        except Exception as exc:
            return {"ok": False,
                    "error": f"guest:{type(exc).__name__}:{exc}"}
    if cmd == "release-all":
        return qmp.call("input-send-event",
                        {"events": _release_events()})
    if cmd == "screendump":
        if not isinstance(args.get("filename"), str):
            raise ValueError("screendump: filename required")
        args = dict(args)
        args["filename"] = _confined(env_dir, args["filename"])
    fn = lambda c, a: qmp.call(c, a)  # noqa: E731
    if journal is not None:
        return journal.execute(obj.get("request_id"), cmd,
                               args if args else None, fn)
    return fn(cmd, args if args else None)


def _read_request(conn):
    buf = b""
    while b"\n" not in buf:
        chunk = conn.recv(65536)
        if not chunk:
            return None
        buf += chunk
        if len(buf) > 1 << 20:
            raise ValueError("request_too_large")
    return json.loads(buf.split(b"\n", 1)[0])


def _bind_listener(env_dir):
    """Per-env IPC endpoint. AF_UNIX where available; else loopback TCP
    with a 128-bit token living only in the private env dir — the gate
    forwards allowlisted QMP ops only, it is NOT a raw QMP proxy."""
    if hasattr(socket, "AF_UNIX"):
        sock_path = env_dir / "qmp.ipc"
        # sun_path ~104-108B — deep env dirs (pytest tmp, CI) overflow it
        if len(str(sock_path).encode()) < 100:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.bind(str(sock_path))
            return s, {"socket": str(sock_path),
                       "transport": "unix"}, None
    import secrets
    token = secrets.token_hex(16)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    return s, {"socket": f"tcp://127.0.0.1:{port}",
               "transport": "tcp", "token": token}, token


def serve(env_dir, spawn=None, poll_s=0.2):
    """Spawn QEMU per spec.approved.json, negotiate QMP, then serve the
    IPC socket until the VM or the daemon dies."""
    import subprocess
    spawn = spawn or (lambda argv, **kw: subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True))
    env_dir = Path(env_dir)
    spec = json.loads((env_dir / "spec.approved.json")
                      .read_text("utf-8"))
    argv = cu_env.build_qemu_argv(spec, Path(env_dir) / "overlay.qcow2")
    proc = spawn(argv)
    sock_path = env_dir / "qmp.ipc"

    def _cleanup():
        try:
            proc.kill()
        except Exception:
            pass
        for f in (sock_path, env_dir / "ready.json"):
            try:
                f.unlink()
            except OSError:
                pass

    atexit.register(_cleanup)
    sup = Supervisor(proc)
    sup.negotiate()

    lsock, ready, token = _bind_listener(env_dir)
    lsock.listen(4)
    lsock.settimeout(poll_s)
    ready.update({"daemon_pid": os.getpid(), "qemu_pid": proc.pid})
    (env_dir / "ready.json").write_text(
        json.dumps(ready), encoding="utf-8")

    journal = Journal(env_dir / "requests.jsonl")
    import threading
    hb_stop = threading.Event()

    # virtio-serial worker pipe (spec opt-in). QEMU opens both ends at
    # start; handshake happens in the background — the guest worker only
    # exists after boot+login, which can take minutes. Caps land in
    # ready.json when they arrive.
    guest = {"channel": None, "caps": None}
    if spec.get("guest_worker"):
        def _guest_handshake():
            import cu_guest
            try:
                rd = open(env_dir / "gwport.out", "rb", buffering=0)
                wr = open(env_dir / "gwport.in", "wb", buffering=0)
                ch = cu_guest.GuestChannel(rd, wr, timeout_s=120)
                raw = ch._read_line()
                hello = json.loads(raw).get("hello") or {}
                guest["caps"] = cu_guest.validate_handshake(hello)
                guest["channel"] = ch
                try:
                    rj = json.loads(
                        (env_dir / "ready.json").read_text("utf-8"))
                    rj["guest_caps"] = guest["caps"]
                    (env_dir / "ready.json").write_text(
                        json.dumps(rj), encoding="utf-8")
                except (OSError, json.JSONDecodeError):
                    pass
            except Exception:
                guest["channel"] = None

        threading.Thread(target=_guest_handshake, daemon=True).start()

    def _beat():
        hb = env_dir / "hb"
        while not hb_stop.is_set() and proc.poll() is None:
            try:
                hb.write_text(str(time.time()))
            except OSError:
                pass
            hb_stop.wait(1.0)

    threading.Thread(target=_beat, daemon=True).start()

    while proc.poll() is None:
        try:
            conn, _ = lsock.accept()
        except socket.timeout:
            continue
        with conn:
            try:
                obj = _read_request(conn)
                if obj is None:
                    continue
                if token is not None and obj.get("token") != token:
                    resp = {"ok": False, "error": "unauthorized"}
                else:
                    result = _handle(sup.qmp, obj, env_dir, journal,
                                     guest["channel"])
                    resp = (result if isinstance(result, dict)
                            and "ok" in result
                            else {"ok": True, "return": result})
                    if obj.get("request_id") is not None:
                        resp["request_id"] = obj["request_id"]
            except cu_qmp.QmpRefused as exc:
                resp = {"ok": False, "error_class": exc.cls,
                        "error": str(exc)}
            except Exception as exc:
                resp = {"ok": False,
                        "error": f"{type(exc).__name__}:{exc}"}
            conn.sendall(json.dumps(resp).encode("utf-8") + b"\n")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="cu_env_daemon")
    ap.add_argument("--env-dir", required=True)
    args = ap.parse_args(argv)
    try:
        serve(args.env_dir)
    except Exception:
        import traceback
        try:
            Path(args.env_dir, "daemon-error.txt").write_text(
                traceback.format_exc(), encoding="utf-8")
        except OSError:
            pass
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
