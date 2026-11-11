#!/usr/bin/env python3
"""api-bridge - OpenAI-compatible local API over the devin CLI.

Issue #478: devin exposes non-standard surfaces (acp stdio, -p print);
harnesses (opencode, hermes, etc.) speak the OpenAI chat-completions
shape. This adapter translates one into the other and serves it on
localhost or the LAN.

  POST /v1/chat/completions  {"model","messages":[{role,content}],"stream"}
  GET  /v1/models            model list parsed from `devin models`
  GET  /health               liveness

Each request spawns `devin -p` in an isolated --workdir so project
context (rules/skills) does not bleed into translations. Streaming is
honest: devin -p flushes once, so stream=true emits a single delta +
[DONE] rather than fake token chunks.

Security: loopback bind needs no auth; any non-loopback bind REQUIRES
--token and enforces `Authorization: Bearer <token>` on every request.

Stdlib only.
Usage:
  bridge.py serve [--bind 127.0.0.1] [--port 8787] [--token T]
                  [--devin PATH] [--workdir DIR] [--timeout 300]
  bridge.py models [--devin PATH]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_CF = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _devin_path(override=None):
    p = (override or os.environ.get("DEVIN_BIN")
         or shutil.which("devin") or shutil.which("devin.exe"))
    if not p:
        sys.exit("devin CLI not found on PATH; pass --devin or set DEVIN_BIN")
    return p


def _flatten(messages):
    """OpenAI messages[] -> a single prompt transcript."""
    sys_parts, turns = [], []
    for m in messages:
        role, content = m.get("role", "user"), m.get("content", "")
        if isinstance(content, list):  # multipart content -> text parts
            content = "".join(p.get("text", "") for p in content
                              if isinstance(p, dict))
        if role == "system":
            sys_parts.append(content)
        elif role == "assistant":
            turns.append(f"Assistant: {content}")
        else:
            turns.append(f"User: {content}")
    prompt = ""
    if sys_parts:
        prompt += "System instructions:\n" + "\n".join(sys_parts) + "\n\n"
    prompt += "\n".join(turns)
    if len(turns) > 1:
        prompt += ("\n\nContinue the conversation as the assistant. "
                   "Reply only with the assistant's next message.")
    return prompt


def _run_devin(devin, prompt, model, workdir, timeout):
    cmd = [devin, "-p", prompt]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              cwd=workdir, timeout=timeout,
                              creationflags=_CF)
    except subprocess.TimeoutExpired:
        return None, ("timeout", f"devin timed out after {timeout}s")
    except OSError as e:
        return None, ("upstream", f"devin spawn failed: {e}")
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "devin failed")[-400:]
        kind = ("model_error" if "model" in msg.lower()
                else "upstream")
        return None, (kind, msg)
    return proc.stdout.strip(), None


def _est_tokens(text):
    """~4 chars/token estimate — devin -p exposes no usage surface."""
    return max(1, len(text or "") // 4)


class AcpBackend:
    """Warm `devin acp` stdio process (#489).

    Real wins over `-p`: incremental agent_message_chunk deltas (true
    streaming) and real token usage in the prompt result. One process,
    serialized — an ACP session is a single conversation so parallel
    prompts would interleave; a fresh session/new per request keeps the
    bridge stateless like the OpenAI contract. Session reuse (keyed
    pooling) stays deferred.
    """

    def __init__(self, devin, workdir, timeout, model=None):
        self.devin, self.workdir = devin, workdir
        self.timeout, self.model = timeout, model
        self._lock = threading.Lock()
        self._proc = self._q = self._seq = None

    def _spawn(self):
        import queue
        cmd = [self.devin, "acp"]
        if self.model:
            cmd += ["--model", self.model]
        self._proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
            errors="replace", bufsize=1, cwd=self.workdir,
            creationflags=_CF)
        self._q, self._seq = queue.Queue(), 0
        threading.Thread(
            target=lambda: [self._q.put(l) for l in self._proc.stdout],
            daemon=True).start()
        rid = self._rpc("initialize", {"protocolVersion": 1,
                                       "clientCapabilities": {"fs": {
                                           "readTextFile": True,
                                           "writeTextFile": False}}})
        for m in self._read(15):
            if m.get("id") == rid:
                break
        self._rpc("initialized", {}, notify=True)

    def _rpc(self, method, params=None, notify=False):
        self._seq += 1
        msg = {"jsonrpc": "2.0", "method": method}
        if not notify:
            msg["id"] = self._seq
        if params is not None:
            msg["params"] = params
        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()
        return msg.get("id")

    def _read(self, timeout):
        """Lines until timeout; yields parsed dicts, skipping blanks."""
        t0 = time.time()
        import queue as _q
        while time.time() - t0 < timeout:
            try:
                ln = self._q.get(
                    timeout=max(1, timeout - (time.time() - t0))).strip()
            except _q.Empty:
                return
            if not ln:
                continue
            try:
                yield json.loads(ln)
            except ValueError:
                continue

    def _answer_fs(self, msg):
        """Agent may request fs/read_text_file mid-prompt — answer it
        or the session deadlocks (verified live)."""
        rid = msg.get("id")
        if msg.get("method") == "fs/read_text_file" and rid:
            path = (msg.get("params") or {}).get("path", "")
            try:
                body = open(path, encoding="utf-8",
                            errors="replace").read()
                res = {"content": body}
            except OSError:
                res = {"error": {"code": -32603, "message": "unreadable"}}
            self._proc.stdin.write(json.dumps(
                {"jsonrpc": "2.0", "id": rid, "result": res}) + "\n")
            self._proc.stdin.flush()

    def prompt(self, text, on_delta=None):
        """Returns (full_text, usage, err). on_delta(str) streams live."""
        with self._lock:
            try:
                if self._proc is None or self._proc.poll() is not None:
                    self._spawn()
            except OSError as e:
                return "", None, ("upstream", f"acp spawn failed: {e}")
            try:
                sid_r = self._rpc("session/new", {
                    "cwd": self.workdir, "mcpServers": []})
                sid = None
                for m in self._read(30):
                    if m.get("id") == sid_r:
                        sid = ((m.get("result") or {})
                               .get("sessionId"))
                        break
                if not sid:
                    return "", None, ("timeout", "acp session/new timeout")
                rid = self._rpc("session/prompt", {
                    "sessionId": sid,
                    "prompt": [{"type": "text", "text": text}]})
                parts, usage, stop = [], None, "end_turn"
                for m in self._read(self.timeout):
                    self._answer_fs(m)
                    upd = (m.get("params") or {}).get("update") or {}
                    if upd.get("sessionUpdate") == "agent_message_chunk":
                        delta = (upd.get("content") or {}).get("text", "")
                        parts.append(delta)
                        if on_delta and delta:
                            on_delta(delta)
                    if m.get("id") == rid:
                        res = m.get("result") or {}
                        u = res.get("usage") or {}
                        usage = {
                            "prompt_tokens": u.get("inputTokens", 0),
                            "completion_tokens": u.get("outputTokens", 0),
                            "total_tokens": u.get("totalTokens", 0)}
                        stop = res.get("stopReason", "end_turn")
                        break
                else:
                    return "", None, ("timeout",
                                      f"acp prompt >{self.timeout}s")
                full = "".join(parts)
                if not full:
                    return "", None, ("upstream", "acp empty response")
                return full, usage, None
            except (BrokenPipeError, OSError) as e:
                self._proc = None
                return "", None, ("upstream", f"acp pipe died: {e}")

    def close(self):
        try:
            if self._proc:
                self._proc.kill()
        except OSError:
            pass


# OpenAI params `devin -p` cannot honour — surfaced, never silently dropped
_UNSUPPORTED = ("temperature", "top_p", "max_tokens", "n", "stop",
                "presence_penalty", "frequency_penalty", "logit_bias",
                "seed", "logprobs", "tools", "tool_choice",
                "response_format")


def _completion(text, model, cid=None, prompt="", ignored=None,
                usage=None):
    out = {
        "id": cid or f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model or "devin",
        "choices": [{"index": 0,
                     "message": {"role": "assistant", "content": text},
                     "finish_reason": "stop"}],
        "usage": usage or {
            "prompt_tokens": _est_tokens(prompt),
            "completion_tokens": _est_tokens(text),
            "total_tokens": _est_tokens(prompt) + _est_tokens(text)},
    }
    if ignored:
        out["x-ignored-params"] = ignored
    return out


def _chunk(text, model, cid):
    return {"id": cid, "object": "chat.completion.chunk",
            "created": int(time.time()), "model": model or "devin",
            "choices": [{"index": 0,
                         "delta": {"role": "assistant", "content": text},
                         "finish_reason": None}]}


def _list_models(devin, workdir, timeout=30):
    try:
        proc = subprocess.run([devin, "models"], capture_output=True,
                              text=True, encoding="utf-8",
                              errors="replace", cwd=workdir,
                              timeout=timeout, creationflags=_CF)
    except (OSError, subprocess.TimeoutExpired):
        return []
    ids = []
    for line in proc.stdout.splitlines():
        s = line.strip()
        if s and not s.startswith(("Available", " ", "(")) \
                and "  " in s:
            first = s.split()[0]
            if first and not first.startswith(("aliases:", "—")):
                ids.append(first)
    return ids or ["devin"]


class Handler(BaseHTTPRequestHandler):
    server_version = "devin-api-bridge/0.1"
    protocol_version = "HTTP/1.1"

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self):
        tok = self.server.token
        if not tok:
            return True
        return self.headers.get("Authorization") == f"Bearer {tok}"

    def _unauth(self):
        self._json(401, {"error": {"message": "unauthorized",
                                   "type": "auth_error"}})

    def log_message(self, fmt, *args):
        sys.stderr.write("[bridge] " + fmt % args + "\n")

    def _cors(self):
        # browser harnesses preflight; loopback LAN use needs explicit
        # origin pass-through — permissive is fine: data stays local
        self.send_header("Access-Control-Allow-Origin",
                         self.headers.get("Origin", "*"))
        self.send_header("Access-Control-Allow-Headers",
                         "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods",
                         "GET, POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if not self._auth_ok():
            return self._unauth()
        if self.path == "/":
            sv = self.server
            return self._json(200, {
                "service": "devin-api-bridge",
                "backend": ("acp" if getattr(sv, "acp", None)
                            else f"{sv.devin} -p"),
                "endpoints": {"GET /health": "liveness",
                              "GET /v1/models": "model inventory",
                              "POST /v1/chat/completions":
                                  "OpenAI-compatible chat (stream via SSE)"},
                "models": len(sv.models),
                "concurrency": sv.concurrency,
                "unsupported-params": list(_UNSUPPORTED)})
        if self.path == "/health":
            sv = self.server
            # depth over liveness: bridge alive != backend reachable —
            # harnesses should be able to tell which half is down
            backend = os.path.isfile(sv.devin) or \
                shutil.which(sv.devin) is not None
            return self._json(200 if backend else 503, {
                "ok": backend,
                "backend": {"path": sv.devin, "found": backend,
                            "models": len(sv.models)}})
        if self.path == "/v1/models":
            ids = self.server.models or ["devin"]
            return self._json(200, {
                "object": "list",
                "data": [{"id": i, "object": "model",
                          "created": 0, "owned_by": "devin"}
                         for i in ids]})
        self._json(404, {"error": {"message": "not found",
                                   "type": "invalid_request_error"}})

    def do_POST(self):
        if not self._auth_ok():
            return self._unauth()
        if self.path != "/v1/chat/completions":
            return self._json(404, {"error": {"message": "not found",
                                       "type": "invalid_request_error"}})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, OSError):
            return self._json(400, {"error": {"message": "bad json",
                                       "type": "invalid_request_error"}})
        messages = req.get("messages") or []
        if not isinstance(messages, list) or not messages:
            return self._json(400, {"error": {
                "message": "messages must be a non-empty array",
                "type": "invalid_request_error"}})
        model = req.get("model")
        sv = self.server
        if model and sv.models and model not in sv.models \
                and model != "devin":
            return self._json(400, {"error": {
                "message": f"unknown model '{model}'",
                "type": "invalid_request_error",
                "param": "model",
                "hint": "GET /v1/models lists valid ids "
                        f"({len(sv.models)} available)"}})
        prompt = _flatten(messages)
        # "devin" is a compat alias, not a real model id — resolve to the
        # CLI's configured default by omitting --model entirely
        backend_model = None if model == "devin" else model
        cid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        if getattr(sv, "acp", None):
            if req.get("stream"):
                return self._sse_acp(sv, prompt, model, cid)
            with sv.sem:
                text, usage, err = sv.acp.prompt(prompt)
        else:
            usage = None
            # concurrent harness fire would spawn N devin processes —
            # cap and queue so the box doesn't melt
            with sv.sem:
                text, err = _run_devin(sv.devin, prompt, backend_model,
                                       sv.workdir, sv.timeout)
        if err:
            kind, msg = err
            code = 504 if kind == "timeout" else 502
            return self._json(code, {"error": {"message": msg,
                                               "type": kind + "_error"}})
        if req.get("stream"):
            self._sse_head()
            line = "data: " + json.dumps(_chunk(text, model, cid)) + "\n\n"
            self.wfile.write(line.encode("utf-8"))
            self._sse_tail(model, cid)
            return
        self._json(200, _completion(
            text, model, cid, prompt=prompt, usage=usage,
            ignored=[k for k in _UNSUPPORTED if k in req]))

    def _sse_head(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

    def _sse_tail(self, model, cid):
        end = _chunk("", model, cid)
        end["choices"][0]["finish_reason"] = "stop"
        end["choices"][0]["delta"] = {}
        self.wfile.write(("data: " + json.dumps(end)
                          + "\n\ndata: [DONE]\n\n").encode("utf-8"))
        self.wfile.flush()

    def _sse_acp(self, sv, prompt, model, cid):
        """True incremental SSE: each agent_message_chunk becomes a
        delta as it arrives (#489)."""
        deltas, err_box = [], [None]

        def feed(d):
            deltas.append(d)
            line = "data: " + json.dumps(
                _chunk(d, model, cid)) + "\n\n"
            self.wfile.write(line.encode("utf-8"))
            self.wfile.flush()

        with sv.sem:
            self._sse_head()
            _, _, err_box[0] = sv.acp.prompt(prompt, on_delta=feed)
        if err_box[0]:
            kind, msg = err_box[0]
            self.wfile.write(("data: " + json.dumps(
                {"error": {"message": msg, "type": kind + "_error"}})
                + "\n\n").encode("utf-8"))
        self._sse_tail(model, cid)


def serve(args):
    devin = _devin_path(args.devin)
    loopback = args.bind in ("127.0.0.1", "localhost", "::1")
    if not loopback and not args.token:
        sys.exit("refusing LAN bind without --token (least privilege)")
    workdir = args.workdir or tempfile.mkdtemp(prefix="devin-bridge-")
    os.makedirs(workdir, exist_ok=True)
    httpd = ThreadingHTTPServer((args.bind, args.port), Handler)
    httpd.devin, httpd.workdir = devin, workdir
    httpd.timeout, httpd.token = args.timeout, args.token
    httpd.models = _list_models(devin, workdir)
    httpd.concurrency = max(1, args.concurrency)
    httpd.sem = threading.BoundedSemaphore(httpd.concurrency)
    # acp = warm process, real streaming + real usage; one process means
    # effective concurrency 1 regardless of --concurrency
    httpd.acp = (AcpBackend(devin, workdir, args.timeout)
                 if args.backend == "acp" else None)
    sys.stderr.write(f"[bridge] http://{args.bind}:{args.port} "
                     f"backend={args.backend}:{devin} "
                     f"models={len(httpd.models)} "
                     f"auth={'token' if args.token else 'loopback'}\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if httpd.acp:
            httpd.acp.close()


def main():
    ap = argparse.ArgumentParser(prog="api-bridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sv = sub.add_parser("serve")
    sv.add_argument("--bind", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8787)
    sv.add_argument("--token")
    sv.add_argument("--devin")
    sv.add_argument("--workdir")
    sv.add_argument("--timeout", type=int, default=300)
    sv.add_argument("--concurrency", type=int, default=2,
                    help="max simultaneous devin backend calls "
                         "(extras queue)")
    sv.add_argument("--backend", choices=("cli", "acp"), default="cli",
                    help="cli=`devin -p` per request; acp=warm ACP "
                         "process — real incremental streaming + real "
                         "token usage (#489)")
    md = sub.add_parser("models")
    md.add_argument("--devin")
    args = ap.parse_args()
    if args.cmd == "models":
        devin = _devin_path(args.devin)
        print(json.dumps({"ok": True, "models": _list_models(
            devin, tempfile.gettempdir())}))
    else:
        serve(args)


if __name__ == "__main__":
    main()
