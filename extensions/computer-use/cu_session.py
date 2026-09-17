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
import queue
import subprocess
import threading
import time
import uuid


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
