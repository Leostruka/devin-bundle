"""layad — resident TCP decision daemon for laya profiles.

One Router(preload=True) serves every enabled contract profile over
localhost TCP, so per-event consumers (PreToolUse hooks, batch file
scans) pay milliseconds instead of a cold engine build.

Protocol (JSON-lines over the socket):
  line 1 (handshake): {"op": "hello", "auth_token": "<token>"}
    -> {"ok": true, "mode": ..., "pid": ..., "uptime_s": ...} and the
       connection stays open for request envelopes; a wrong token gets
       {"ok": false, "error": "unauthorized"} and the socket closes.
  line 2+: {"version": 1, "request_id": ..., "request": {...§5.1...}}
    -> one recommendation per line (suggestion | abstain), served by
       laya_worker.serve with the same semantics as serve-stdio.

Identity: .devin/laya/daemon.json holds {pid, port, auth_token,
config_sha256, mode, started_at}; the file is removed on shutdown.
auth_token is generated per spawn — callers must read the file, never
assume a token. Idle beyond idle_ttl_s the daemon exits on its own.

Entry point: `python laya_cli.py serve-daemon --config <profile.json>`
Mode "off" exits without loading the engine — off means off.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import socketserver
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc   # noqa: E402
import laya_worker               # noqa: E402

DAEMON_FILE = "daemon.json"
DEFAULT_IDLE_TTL_S = 1800


def _diag(msg):
    print(f"[layad] {msg}", file=sys.stderr)


def config_digest(config_path):
    """sha256 of the profile file bytes; "" when missing — reused by
    ensure_daemon to detect config drift."""
    try:
        return hashlib.sha256(
            Path(config_path).read_bytes()).hexdigest()
    except OSError:
        return ""


class _LockedEngine:
    """predict() calls are serialized — the Router's thread-safety is
    not part of its contract. Locking per call (not per connection)
    keeps a stalled client from blocking the daemon."""
    def __init__(self, engine, lock):
        self._engine = engine
        self._lock = lock

    def predict(self, *args, **kwargs):
        with self._lock:
            return self._engine.predict(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._engine, name)


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def make_handler(engine, config, auth_token, state):
    locked = _LockedEngine(engine, threading.Lock())

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            state["last_req"] = time.monotonic()
            reader = self.request.makefile("r", encoding="utf-8",
                                           newline="\n")
            writer = self.request.makefile("w", encoding="utf-8",
                                           newline="\n")
            try:
                try:
                    hello = json.loads(reader.readline())
                except (json.JSONDecodeError, ValueError):
                    return
                if not isinstance(hello, dict) \
                        or hello.get("op") != "hello" \
                        or hello.get("auth_token") != auth_token:
                    writer.write(json.dumps(
                        {"ok": False, "error": "unauthorized"}) + "\n")
                    writer.flush()
                    return
                writer.write(json.dumps({
                    "ok": True, "pid": os.getpid(),
                    "mode": dc.effective_mode(config),
                    "uptime_s": round(
                        time.monotonic() - state["started"], 1),
                }) + "\n")
                writer.flush()
                # Delegate the request stream to the worker loop.
                laya_worker.serve(reader, writer, locked, config)
            finally:
                state["last_req"] = time.monotonic()
                for f in (reader, writer):
                    try:
                        f.close()
                    except OSError:
                        pass

    return Handler


def _idle_watchdog(server, state, ttl_s):
    while not state["shutdown"]:
        time.sleep(min(30, ttl_s))
        if time.monotonic() - state["last_req"] > ttl_s:
            _diag(f"idle {ttl_s}s; exiting")
            try:
                server.shutdown()
            except Exception:
                pass
            return


def serve_socket(engine, config, *, host="127.0.0.1", port=0,
                 laya_dir=None, config_path=None,
                 idle_ttl_s=DEFAULT_IDLE_TTL_S, auth_token=None):
    """Bind and serve until idle_ttl or SIGTERM. Returns the bound
    port. Testable: caller may inject any engine object."""
    token = auth_token or secrets.token_hex(16)
    state = {"last_req": time.monotonic(), "started": time.monotonic(),
             "shutdown": False}
    server = _Server((host, port), make_handler(engine, config, token,
                                                state))
    bound_port = server.server_address[1]
    if laya_dir:
        info = {"pid": os.getpid(), "port": bound_port,
                "auth_token": token,
                "config_sha256": config_digest(config_path)
                if config_path else "",
                "mode": dc.effective_mode(config),
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        p = Path(laya_dir)
        p.mkdir(parents=True, exist_ok=True)
        (p / DAEMON_FILE).write_text(json.dumps(info), encoding="utf-8")
    threading.Thread(target=_idle_watchdog,
                     args=(server, state, idle_ttl_s),
                     daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        state["shutdown"] = True
        if laya_dir:
            try:
                (Path(laya_dir) / DAEMON_FILE).unlink()
            except OSError:
                pass
        server.server_close()
    return bound_port


def main(config_path=None, host="127.0.0.1", port=0, laya_dir=None):
    cfg = dc.load_config(config_path)
    if not dc.enabled(cfg):
        print(json.dumps({"ok": True, "mode": "off",
                          "note": "feature disabled; engine not loaded"}))
        return 0
    model = cfg.get("model")
    if model and model not in (cfg.get("models") or {}):
        print(json.dumps({"ok": False,
                          "error": f"model_not_approved:{model}"}))
        return 1
    try:
        engine = laya_worker.load_engine(cfg.get("models") or {},
                                        cfg.get("device") or "cpu")
    except RuntimeError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    if laya_dir is None:
        laya_dir = str(Path(config_path).parent) if config_path \
            else str(Path.cwd() / ".devin" / "laya")
    daemon_cfg = cfg.get("daemon") or {}
    ttl = int(daemon_cfg.get("idle_ttl_s") or DEFAULT_IDLE_TTL_S)
    _diag(f"engine loaded; serving {host}:{port or 'auto'}")
    serve_socket(engine, cfg, host=host, port=port,
                 laya_dir=laya_dir, config_path=config_path,
                 idle_ttl_s=ttl)
    return 0


if __name__ == "__main__":
    cfg_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(cfg_arg))
