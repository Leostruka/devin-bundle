"""decision_client — stdlib client for a resident laya worker.

Owns exactly one subprocess (spawned lazily on first recommend, only
by callers that already checked decision_contract.enabled()). JSON-lines
over the child's stdin/stdout; the child's stderr is inherited so
diagnostics never touch the protocol channel.

Timeout, EOF, malformed or foreign replies -> typed abstention; a
request whose outcome is uncertain is never replayed automatically.
close() terminates only the child it spawned.
"""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc  # noqa: E402


class DecisionClient:
    def __init__(self, argv, timeout_s=5.0):
        self._argv = list(argv)
        self._timeout = float(timeout_s)
        self._proc = None
        self._q = None

    def _read_loop(self, proc, q):
        try:
            for line in proc.stdout:
                q.put(line)
        except (OSError, ValueError):
            pass
        q.put(None)  # EOF / pipe closed

    def _spawn(self):
        if self._proc is not None and self._proc.poll() is None:
            return
        self._kill()
        self._proc = subprocess.Popen(
            self._argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=None, text=True, bufsize=1)
        self._q = queue.Queue()
        threading.Thread(target=self._read_loop,
                         args=(self._proc, self._q),
                         daemon=True).start()

    def _kill(self):
        if self._proc is None:
            return
        try:
            if self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
        except OSError:
            pass
        self._proc = None

    def recommend(self, request):
        rid = str(request.get("request_id", "")) \
            if isinstance(request, dict) else ""
        errs = dc.validate_request(request)
        if errs:
            return dc.make_abstention(rid, "invalid_request:" + errs[0])
        try:
            self._spawn()
            self._proc.stdin.write(json.dumps(
                {"version": 1, "request_id": rid,
                 "request": request}, ensure_ascii=False) + "\n")
            self._proc.stdin.flush()
        except (OSError, ValueError):
            self._kill()
            return dc.make_abstention(rid, "worker_spawn_failed")
        try:
            line = self._q.get(timeout=self._timeout)
        except queue.Empty:
            self._kill()
            return dc.make_abstention(rid, "worker_timeout")
        if line is None:
            self._kill()
            return dc.make_abstention(rid, "worker_eof")
        try:
            reply = json.loads(line)
        except json.JSONDecodeError:
            return dc.make_abstention(rid, "worker_protocol_error")
        if not isinstance(reply, dict) \
                or reply.get("request_id") != rid:
            return dc.make_abstention(rid, "worker_protocol_error")
        rerrs = dc.validate_recommendation(reply, request)
        if rerrs:
            bad = dc.make_abstention(rid,
                                     "worker_protocol_error:" + rerrs[0])
            bad["context"] = dict(request.get("context") or {})
            return bad
        return reply

    def close(self):
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.stdin.close()
            except OSError:
                pass
        self._kill()
