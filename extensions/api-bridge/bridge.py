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


def _completion(text, model, cid=None, prompt=""):
    return {
        "id": cid or f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model or "devin",
        "choices": [{"index": 0,
                     "message": {"role": "assistant", "content": text},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": _est_tokens(prompt),
                  "completion_tokens": _est_tokens(text),
                  "total_tokens": _est_tokens(prompt) + _est_tokens(text)},
    }


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

    def do_GET(self):
        if not self._auth_ok():
            return self._unauth()
        if self.path == "/health":
            return self._json(200, {"ok": True})
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
        text, err = _run_devin(sv.devin, prompt, model, sv.workdir,
                               sv.timeout)
        if err:
            kind, msg = err
            code = 504 if kind == "timeout" else 502
            return self._json(code, {"error": {"message": msg,
                                               "type": kind + "_error"}})
        cid = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        if req.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            line = "data: " + json.dumps(_chunk(text, model, cid)) + "\n\n"
            self.wfile.write(line.encode("utf-8"))
            end = _chunk("", model, cid)
            end["choices"][0]["finish_reason"] = "stop"
            end["choices"][0]["delta"] = {}
            self.wfile.write(("data: " + json.dumps(end)
                              + "\n\ndata: [DONE]\n\n").encode("utf-8"))
            self.wfile.flush()
            return
        self._json(200, _completion(text, model, cid, prompt=prompt))


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
    sys.stderr.write(f"[bridge] http://{args.bind}:{args.port} "
                     f"backend={devin} models={len(httpd.models)} "
                     f"auth={'token' if args.token else 'loopback'}\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


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
