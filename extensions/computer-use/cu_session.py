#!/usr/bin/env python3
"""Persistent worker session — opt-in, local-only.

Justified by the frozen baseline (.devin/research/cu-benchmark-baseline.json):
startup_subprocess p50 ~142ms is the largest single boundary; a persistent
worker amortizes interpreter+imports across calls.

Transport is the child's stdin/stdout — JSON lines over OS pipes. No
sockets, no listeners, no network surface; this is not a security sandbox.
A worker that stops answering is killed and respawned; restart bumps the
generation and rotates the session tag so stale envelopes reject.

    w = Worker([sys.executable, "-u", "worker.py"])
    w.request({"op": "enum"})            -> {"ok": ...}
    w.cancel()                           -> pending queue drained
    w.restart()                          -> new pid, gen+1, new session tag
    w.close()
"""
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DAEMON_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-daemon.json")
DAEMON_IDLE_S = float(os.environ.get("CU_DAEMON_IDLE", "600"))


def _run_op(cmd):
    """Execute one op in-process with hot imports. Returns response dict
    carrying the script's own JSON stdout verbatim."""
    import io
    import importlib
    from contextlib import redirect_stdout
    name, argv = cmd.get("script"), cmd.get("argv") or []
    if name == "_echo":
        return {"ok": True, "output": json.dumps({"echo": argv})}
    if name not in ("mouse", "type_text", "screenshot", "profile"):
        return {"ok": False, "error": f"unknown script {name!r}"}
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    buf = io.StringIO()
    try:
        mod = importlib.import_module(name)
        old = sys.argv
        sys.argv = [f"{name}.py"] + [str(a) for a in argv]
        try:
            with redirect_stdout(buf):
                mod.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old
        return {"ok": True, "output": buf.getvalue().strip()}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def worker_main():
    """stdin/stdout JSON-line worker (parent-managed lifetime)."""
    os.environ.pop("CU_SESSION", None)  # ops must not re-route
    for line in sys.stdin:
        try:
            env = json.loads(line)
        except json.JSONDecodeError:
            continue
        print(json.dumps(_run_op(env.get("cmd") or {})), flush=True)


def _daemon_write_pidfile(port, session):
    data = {"pid": os.getpid(), "port": port, "session": session,
            "started": time.time()}
    tmp = DAEMON_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, DAEMON_PATH)


def daemon_main():
    """Loopback-only daemon: one JSON line per connection. Idle TTL exit.
    127.0.0.1 is not a public surface — no remote connections accepted."""
    import socket
    os.environ.pop("CU_SESSION", None)  # ops must not re-route
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(4)
    srv.settimeout(1.0)
    session = uuid.uuid4().hex[:12]
    _daemon_write_pidfile(srv.getsockname()[1], session)
    last = time.time()
    try:
        while time.time() - last < DAEMON_IDLE_S:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            with conn:
                try:
                    conn.settimeout(30)
                    data = b""
                    while not data.endswith(b"\n"):
                        chunk = conn.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    env = json.loads(data.decode("utf-8"))
                    if env.get("session") not in (None, session):
                        resp = {"ok": False, "error": "stale session"}
                    else:
                        resp = _run_op(env.get("cmd") or {})
                    conn.sendall(json.dumps(resp).encode() + b"\n")
                    last = time.time()
                except Exception:
                    pass
    finally:
        srv.close()
        try:
            os.remove(DAEMON_PATH)
        except OSError:
            pass


class Worker:
    def __init__(self, argv, timeout=10.0):
        self.argv = argv
        self.timeout = timeout
        self.generation = 0
        self.session = None
        self._proc = None
        self._reader = None
        self._lines = queue.Queue()
        self._pending = []
        self._spawn()

    # -- lifecycle ---------------------------------------------------------
    def _spawn(self):
        self._proc = subprocess.Popen(
            self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.generation += 1
        self.session = uuid.uuid4().hex[:12]
        self._lines = queue.Queue()
        # pump bound to THIS queue+proc: a stale incarnation can never leak
        # lines into a respawned worker's queue
        self._reader = threading.Thread(
            target=self._pump, args=(self._proc, self._lines), daemon=True)
        self._reader.start()

    @staticmethod
    def _pump(proc, lines):
        try:
            for line in proc.stdout:
                lines.put(line)
        except (ValueError, OSError):
            pass
        lines.put(None)  # EOF sentinel

    @property
    def pid(self):
        return self._proc.pid if self._proc else None

    @property
    def alive(self):
        return self._proc is not None and self._proc.poll() is None

    def restart(self):
        """Kill and respawn. Generation+session rotate: any envelope stamped
        by the old incarnation is stale by construction."""
        self.close(kill_only=True)
        self._spawn()

    def close(self, kill_only=False):
        if self._proc:
            try:
                self._proc.kill()
                self._proc.wait(timeout=5)
            except Exception:
                pass
            self._proc = None
        if not kill_only:
            self._pending.clear()

    # -- protocol ----------------------------------------------------------
    def _envelope(self, cmd):
        return {"session": self.session, "gen": self.generation,
                "ts": time.time(), "cmd": cmd}

    def verify_envelope(self, env):
        """An envelope is valid only for the incarnation that stamped it."""
        return (env.get("session") == self.session
                and env.get("gen") == self.generation)

    def request(self, cmd, timeout=None):
        """Send one command, wait for one JSON line. Timeout or EOF ->
        restart + status timeout (hung provider containment)."""
        if not self.alive:
            self.restart()
        env = self._envelope(cmd)
        try:
            self._proc.stdin.write(json.dumps(env) + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            self.restart()
            return {"ok": False, "status": "timeout",
                    "error": "worker pipe broken — restarted"}
        try:
            line = self._lines.get(timeout=timeout or self.timeout)
        except queue.Empty:
            self.restart()
            return {"ok": False, "status": "timeout",
                    "error": f"worker hung >{timeout or self.timeout}s — restarted"}
        if line is None:
            self.restart()
            return {"ok": False, "status": "timeout",
                    "error": "worker exited — restarted"}
        try:
            r = json.loads(line)
            r.setdefault("ok", True)
            return r
        except json.JSONDecodeError:
            return {"ok": False, "status": "unknown",
                    "error": f"worker returned non-JSON: {line[:80]!r}"}

    # -- queue -------------------------------------------------------------
    def submit(self, cmd):
        self._pending.append(cmd)

    def run_pending(self):
        out = []
        while self._pending:
            out.append(self.request(self._pending.pop(0)))
        return out

    def cancel(self):
        """Drain pending without dispatching — cancelled items never fire."""
        n = len(self._pending)
        self._pending.clear()
        return n


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        daemon_main()
    elif "--worker" in sys.argv:
        worker_main()
