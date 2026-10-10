"""laya_client — thin TCP client for the resident layad daemon.

Mirrors decision_client semantics: typed abstention on any failure
(daemon down, timeout, malformed or foreign reply, wrong token), never
raises on the hot path, never replays an uncertain request.

ensure_daemon() lazily spawns `laya_cli.py serve-daemon` behind a lock
file so concurrent hooks do not stampede; a daemon whose config_sha256
no longer matches the on-disk profile is recycled.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc   # noqa: E402
import layad                      # noqa: E402

LAYA_DIRNAME = "laya"
DAEMON_FILE = "daemon.json"
LOCK_FILE = "daemon.lock"
LOCK_STALE_S = 120


def devin_home():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


def default_config_path():
    """Project profile first, then the installed user-level one."""
    for base in (os.environ.get("DEVIN_PROJECT_DIR"), os.getcwd(),
                 devin_home()):
        if not base:
            continue
        p = os.path.join(base, ".devin", LAYA_DIRNAME, "profile.json")
        if os.path.isfile(p):
            return p
        p = os.path.join(base, LAYA_DIRNAME, "profile.json")
        if os.path.isfile(p):
            return p
    return os.path.join(os.getcwd(), ".devin", LAYA_DIRNAME,
                        "profile.json")


def read_daemon_info(laya_dir):
    try:
        info = json.loads(
            (Path(laya_dir) / DAEMON_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(info, dict) or not info.get("port") \
            or not info.get("auth_token"):
        return None
    return info


def _pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        ctypes.windll.kernel32.CloseHandle(h)
        return True
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _port_open(host, port, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _spawn_daemon(config_path, laya_dir):
    here = Path(__file__).resolve()
    venv_py = here.parent / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python")
    py = str(venv_py) if venv_py.is_file() else sys.executable
    cli = here.parent / "laya_cli.py"
    subprocess.Popen(
        [py, str(cli), "serve-daemon", "--config", config_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if os.name == "nt" else 0,
        start_new_session=os.name != "nt")


def _terminate(pid):
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, timeout=10)
        else:
            os.kill(pid, 15)
    except (OSError, subprocess.SubprocessError):
        pass


def ensure_daemon(config_path=None, *, spawn_timeout_s=60.0):
    """Return daemon info dict when a compatible layad is serving,
    else None. Lazy-spawns behind a lock file; recycles on config
    digest mismatch. Never raises."""
    if os.environ.get("LAYA_NO_DAEMON"):
        return None
    config_path = config_path or default_config_path()
    laya_dir = str(Path(config_path).parent)
    want_sha = layad.config_digest(config_path)

    info = read_daemon_info(laya_dir)
    if info and info.get("config_sha256") == want_sha \
            and _pid_alive(info.get("pid", -1)) \
            and _port_open("127.0.0.1", int(info["port"])):
        return info
    if info and _pid_alive(info.get("pid", -1)):
        _terminate(int(info["pid"]))  # stale config: recycle
        info = None

    lock_path = Path(laya_dir) / LOCK_FILE
    Path(laya_dir).mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        acquired = True
    except OSError:
        acquired = False
    if not acquired:
        # Another process is spawning; wait for it, then re-check.
        try:
            stale = time.time() - lock_path.stat().st_mtime > LOCK_STALE_S
        except OSError:
            stale = True
        if stale:
            try:
                lock_path.unlink()
            except OSError:
                pass
        deadline = time.time() + spawn_timeout_s
        while time.time() < deadline:
            info = read_daemon_info(laya_dir)
            if info and info.get("config_sha256") == want_sha \
                    and _port_open("127.0.0.1", int(info["port"])):
                return info
            time.sleep(0.5)
        return None
    try:
        # Re-check inside the lock: winner may have just finished.
        info = read_daemon_info(laya_dir)
        if info and info.get("config_sha256") == want_sha \
                and _pid_alive(info.get("pid", -1)) \
                and _port_open("127.0.0.1", int(info["port"])):
            return info
        _spawn_daemon(config_path, laya_dir)
        deadline = time.time() + spawn_timeout_s
        while time.time() < deadline:
            info = read_daemon_info(laya_dir)
            if info and _port_open("127.0.0.1", int(info["port"])):
                return info
            time.sleep(0.5)
        return None
    finally:
        try:
            lock_path.unlink()
        except OSError:
            pass


def recommend(request, daemon=None, timeout_s=5.0):
    """One §5.1 request over one short-lived connection. Returns a
    recommendation dict or a typed abstention; never raises."""
    rid = str(request.get("request_id", "")) \
        if isinstance(request, dict) else ""
    errs = dc.validate_request(request)
    if errs:
        return dc.make_abstention(rid, "invalid_request:" + errs[0])
    if daemon is None:
        return dc.make_abstention(rid, "daemon_unavailable")
    try:
        sock = socket.create_connection(
            ("127.0.0.1", int(daemon["port"])), timeout=timeout_s)
        sock.settimeout(timeout_s)
        rf = sock.makefile("r", encoding="utf-8", newline="\n")
        wf = sock.makefile("w", encoding="utf-8", newline="\n")
        try:
            wf.write(json.dumps(
                {"op": "hello",
                 "auth_token": daemon["auth_token"]}) + "\n")
            wf.write(json.dumps(
                {"version": 1, "request_id": rid,
                 "request": request}, ensure_ascii=False) + "\n")
            wf.flush()
            hello = json.loads(rf.readline())
            if not isinstance(hello, dict) or not hello.get("ok"):
                return dc.make_abstention(rid, "daemon_unauthorized")
            line = rf.readline()
        finally:
            for f in (rf, wf):
                try:
                    f.close()
                except OSError:
                    pass
            sock.close()
    except (OSError, ValueError, socket.timeout):
        return dc.make_abstention(rid, "daemon_unreachable")
    try:
        reply = json.loads(line)
    except (json.JSONDecodeError, UnboundLocalError):
        return dc.make_abstention(rid, "daemon_protocol_error")
    if not isinstance(reply, dict) or reply.get("request_id") != rid:
        return dc.make_abstention(rid, "daemon_protocol_error")
    rerrs = dc.validate_recommendation(reply, request)
    if rerrs:
        bad = dc.make_abstention(rid,
                                 "daemon_protocol_error:" + rerrs[0])
        bad["context"] = dict(request.get("context") or {})
        return bad
    return reply


class DaemonSession:
    """One persistent connection for streaming many requests — the
    daemon serializes predict() anyway, so a single socket is the
    cheapest correct transport for batch work."""

    def __init__(self, daemon, timeout_s=10.0):
        self._daemon = daemon
        self._timeout = timeout_s
        self._sock = None
        self._rf = None
        self._wf = None

    def _connect(self):
        if self._sock is not None:
            return True
        try:
            self._sock = socket.create_connection(
                ("127.0.0.1", int(self._daemon["port"])),
                timeout=self._timeout)
            self._sock.settimeout(self._timeout)
            self._rf = self._sock.makefile("r", encoding="utf-8",
                                           newline="\n")
            self._wf = self._sock.makefile("w", encoding="utf-8",
                                           newline="\n")
            self._wf.write(json.dumps(
                {"op": "hello",
                 "auth_token": self._daemon["auth_token"]}) + "\n")
            self._wf.flush()
            hello = json.loads(self._rf.readline())
            if not isinstance(hello, dict) or not hello.get("ok"):
                self.close()
                return False
        except (OSError, ValueError):
            self.close()
            return False
        return True

    def batch(self, requests):
        """Requests in order -> replies in order. Per-item abstention
        on failure; the session stays usable after a bad item."""
        out = []
        if not self._connect():
            for r in requests:
                rid = str(r.get("request_id", "")) \
                    if isinstance(r, dict) else ""
                out.append(dc.make_abstention(rid, "daemon_unreachable"))
            return out
        for req in requests:
            out.append(self._one(req))
        return out

    def _one(self, request):
        rid = str(request.get("request_id", "")) \
            if isinstance(request, dict) else ""
        errs = dc.validate_request(request)
        if errs:
            return dc.make_abstention(rid, "invalid_request:" + errs[0])
        try:
            self._wf.write(json.dumps(
                {"version": 1, "request_id": rid,
                 "request": request}, ensure_ascii=False) + "\n")
            self._wf.flush()
            reply = json.loads(self._rf.readline())
        except (OSError, ValueError, socket.timeout):
            self.close()
            return dc.make_abstention(rid, "daemon_protocol_error")
        if not isinstance(reply, dict) or reply.get("request_id") != rid:
            return dc.make_abstention(rid, "daemon_protocol_error")
        rerrs = dc.validate_recommendation(reply, request)
        if rerrs:
            bad = dc.make_abstention(
                rid, "daemon_protocol_error:" + rerrs[0])
            bad["context"] = dict(request.get("context") or {})
            return bad
        return reply

    def close(self):
        for f in (self._rf, self._wf):
            try:
                if f is not None:
                    f.close()
            except OSError:
                pass
        try:
            if self._sock is not None:
                self._sock.close()
        except OSError:
            pass
        self._sock = self._rf = self._wf = None


def batch(requests, daemon=None, timeout_s=10.0):
    """requests -> replies, same order, over one session."""
    sess = DaemonSession(daemon, timeout_s=timeout_s)
    try:
        return sess.batch(requests)
    finally:
        sess.close()
