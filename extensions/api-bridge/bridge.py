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
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "api-bridge"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


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


# ---- internal backend (undocumented Connect+proto endpoint) ----
# Contract: INTERNAL-PROTOCOL.md — unstable, may break on CLI updates.

def _pb_v(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | 0x80 if n else b)
        if not n:
            return bytes(out)


def _pb_key(num, wt):
    return _pb_v((num << 3) | wt)


def _pb_s(num, text):
    b = text.encode("utf-8")
    return _pb_key(num, 2) + _pb_v(len(b)) + b


def _pb_m(num, body):
    return _pb_key(num, 2) + _pb_v(len(body)) + body


def _pb_vi(num, val):
    return _pb_key(num, 0) + _pb_v(val)


def _pb_varint(b, i):
    v = 0
    s = 0
    while True:
        x = b[i]
        i += 1
        v |= (x & 0x7F) << s
        if not (x & 0x80):
            return v, i
        s += 7


def _pb_fields(b):
    """Yields (field_num, wire_type, value)."""
    i = 0
    while i < len(b):
        key, i = _pb_varint(b, i)
        fn, wt = key >> 3, key & 7
        if wt == 0:
            val, i = _pb_varint(b, i)
            yield fn, wt, val
        elif wt == 2:
            ln, i = _pb_varint(b, i)
            yield fn, wt, b[i:i + ln]
            i += ln
        elif wt == 1:
            yield fn, wt, b[i:i + 8]
            i += 8
        elif wt == 5:
            yield fn, wt, b[i:i + 4]
            i += 4
        else:
            return


def _connect_frames(b):
    """Yields (flags, payload); gunzips flag&1."""
    import gzip
    i = 0
    while i + 5 <= len(b):
        flags = b[i]
        ln = int.from_bytes(b[i + 1:i + 5], "big")
        payload = b[i + 5:i + 5 + ln]
        if flags & 1:
            try:
                payload = gzip.decompress(payload)
            except Exception:
                pass
        yield flags, payload
        i += 5 + ln


def _credentials():
    """(api_key, api_server_url) from credentials.toml or env."""
    key = os.environ.get("DEVIN_API_TOKEN")
    base = os.environ.get("WINDSURF_API_SERVER_URL")
    if not key or not base:
        import re
        home = os.path.expanduser("~")
        toml = os.path.join(home, "AppData", "Roaming", "devin",
                            "credentials.toml")
        if not os.path.isfile(toml):
            toml = os.path.join(home, ".config", "devin",
                                "credentials.toml")
        try:
            txt = open(toml, encoding="utf-8").read()
        except OSError:
            return key, base
        if not key:
            m = re.search(r'windsurf_api_key\s*=\s*"([^"]+)"', txt)
            key = m.group(1) if m else None
        if not base:
            m = re.search(r'api_server_url\s*=\s*"([^"]+)"', txt)
            base = m.group(1) if m else None
    return key, (base or "https://server.codeium.com")


class InternalBackend:
    """Direct Connect+proto client to the CLI's inference endpoint.

    Unlike -p/acp, this returns raw inference: tool_calls deltas reach
    the harness, which drives its own tool loop. Server-sealed state is
    stored and re-injected on follow-up turns (INTERNAL-PROTOCOL.md).
    """

    SERVICE = "/exa.api_server_pb.ApiServerService/GetChatMessage"

    def __init__(self, api_key, base, model_default="swe-2-max",
                 timeout=300):
        self.key = api_key
        self.base = base.rstrip("/")
        self.model_default = model_default
        self.timeout = timeout
        self.seals = {}          # tool_call_id -> {seal, reasoning, model}
        self._slug = "bridge-" + uuid.uuid4().hex[:8]
        self._user = None        # 'user-<id>' fetched once via GetUserStatus

    # -- wire --

    def _post(self, path, body, connect=True):
        import http.client
        auth = base64.b64encode(self.key.encode()).decode()
        host = urllib.parse.urlsplit(self.base).netloc
        scheme = urllib.parse.urlsplit(self.base).scheme
        conn = (http.client.HTTPSConnection if scheme == "https"
                else http.client.HTTPConnection)(host, timeout=self.timeout)
        hdrs = {"authorization": f"Basic {auth}",
                "connect-protocol-version": "1",
                "content-type": ("application/connect+proto" if connect
                                 else "application/proto")}
        conn.request("POST", path, body=body, headers=hdrs)
        resp = conn.getresponse()
        status, data = resp.status, resp.read()
        conn.close()
        return status, data

    def _meta(self):
        inner = b"".join([
            _pb_s(1, "devin-cli"), _pb_s(2, "3000.12.43"),
            _pb_s(3, self.key), _pb_s(4, "en"), _pb_s(5, "windows"),
            _pb_s(7, "3000.12.43"), _pb_s(12, "chisel"),
            _pb_s(28, "chisel")])
        return _pb_m(1, inner)

    def _user_slug(self):
        if self._user is None:
            try:
                st, data = self._post(
                    "/exa.seat_management_pb.SeatManagementService/"
                    "GetUserStatus", self._meta(), connect=False)
                m = re.search(rb"user-[0-9a-f]{32}", data)
                self._user = m.group(0).decode() if st == 200 and m else ""
            except OSError:
                self._user = ""
        return (_pb_s(28, f"{self._user}:{self._slug}")
                if self._user else b"")

    # -- translation --

    def _msg(self, m_):
        role, out = m_.get("role", "user"), b""
        out += _pb_s(1, str(uuid.uuid4()))
        if role == "assistant":
            out += _pb_vi(2, 2)
            if m_.get("content"):
                out += _pb_s(3, _msg_text(m_["content"]))
            for tc in m_.get("tool_calls") or []:
                fn = tc.get("function", {})
                call = (_pb_s(1, tc["id"]) + _pb_s(2, fn.get("name", ""))
                        + _pb_s(3, fn.get("arguments", "") or ""))
                out += _pb_m(6, call)
            seal = None
            for tc in m_.get("tool_calls") or []:
                seal = self.seals.get(tc["id"])
            if seal:
                out += _pb_s(11, seal.get("reasoning") or "")
                out += _pb_s(12, seal["seal"])
                out += _pb_s(18, "sealed")
                out += _pb_s(22, seal.get("model") or self.model_default)
            return _pb_m(3, out)
        if role == "tool":
            out += _pb_vi(2, 4)
            out += _pb_s(3, _msg_text(m_.get("content")))
            if m_.get("tool_call_id"):
                out += _pb_s(7, m_["tool_call_id"])
            out += _pb_m(8, b"\x08\x01")
            return _pb_m(3, out)
        out += _pb_vi(2, 1)
        out += _pb_s(3, _msg_text(m_.get("content")))
        out += _pb_m(8, b"\x08\x01")
        return _pb_m(3, out)

    def _build(self, messages, tools, model):
        parts = [self._meta()]
        sys_txt = "\n\n".join(_msg_text(m_.get("content"))
                              for m_ in messages if m_.get("role") == "system")
        if sys_txt:
            parts.append(_pb_s(2, sys_txt))
        for m_ in messages:
            if m_.get("role") == "system":
                continue
            parts.append(self._msg(m_))
        import struct
        cfg = (_pb_vi(1, 1) + _pb_vi(2, 128000) + _pb_vi(3, 400)
               + _pb_key(5, 1) + struct.pack("<d", 1.0) + _pb_vi(7, 40)
               + _pb_key(8, 1) + struct.pack("<d", 0.93))
        parts += [_pb_vi(7, 5), _pb_m(8, cfg)]
        for t in tools or []:
            fn = t.get("function", {})
            schema = json.dumps(fn.get("parameters") or {})
            parts.append(_pb_m(10, _pb_s(1, fn.get("name", ""))
                               + _pb_s(2, fn.get("description", ""))
                               + _pb_s(3, schema)))
        parts.append(_pb_m(15, _pb_s(1, str(uuid.uuid4()))
                           + _pb_vi(2, 1) + _pb_vi(3, 4)))
        parts += [_pb_s(16, str(uuid.uuid4())), _pb_vi(20, 1),
                  _pb_s(21, model or self.model_default),
                  self._user_slug()]
        req = b"".join(parts)
        return b"\x00" + len(req).to_bytes(4, "big") + req

    # -- public API --

    def prompt(self, messages, tools=None, model=None, on_delta=None):
        """-> (text, tool_calls, usage, err); on_delta(kind,obj) streams."""
        try:
            body = self._build(messages, tools, model)
        except Exception as e:  # noqa: BLE001
            return None, None, None, ("bridge", f"encode failed: {e}")
        try:
            status, raw = self._post(self.SERVICE, body)
        except OSError as e:
            return None, None, None, ("upstream", f"connect failed: {e}")
        text_parts, tcs, usage = [], {}, None
        reasoning_parts = []
        for flags, fr in _connect_frames(raw):
            if flags & 0x82:
                try:
                    err = json.loads(fr)
                    msg = err.get("error", {}).get("message", "")
                    if msg:
                        return None, None, None, ("upstream", msg[:300])
                except ValueError:
                    pass
                continue
            seal_blob = None
            for fn, wt, val in _pb_fields(fr):
                if fn == 3 and wt == 2:
                    d = val.decode("utf-8", "replace")
                    text_parts.append(d)
                    if on_delta:
                        on_delta("text", d)
                elif fn == 6 and wt == 2:
                    tc = {"id": "", "name": "", "args": ""}
                    for cn, cw, cv in _pb_fields(val):
                        if cn in (1, 2, 3) and cw == 2:
                            tc[{1: "id", 2: "name", 3: "args"}[cn]] = \
                                cv.decode("utf-8", "replace")
                    tcs[tc["id"]] = {"id": tc["id"], "type": "function",
                                     "function": {"name": tc["name"],
                                                  "arguments": tc["args"]}}
                    if on_delta:
                        on_delta("tool_call", tcs[tc["id"]])
                elif fn == 7 and wt == 2:
                    u = {fn2: v2 for fn2, wt2, v2 in _pb_fields(val)
                         if wt2 == 0}
                    usage = {
                        "prompt_tokens": u.get(2, 0),
                        "completion_tokens": u.get(3, 0),
                        "total_tokens": u.get(2, 0) + u.get(3, 0)}
                elif fn == 9 and wt == 2:
                    reasoning_parts.append(
                        val.decode("utf-8", "replace"))
                elif fn == 10 and wt == 2 and \
                        val.startswith(b"sealed.v1."):
                    seal_blob = val.decode("utf-8", "replace")
            if seal_blob and tcs:
                last = list(tcs.values())[-1]
                self.seals[last["id"]] = {
                    "seal": seal_blob,
                    "reasoning": "".join(reasoning_parts),
                    "model": model or self.model_default}
        if status != 200:
            return None, None, None, ("upstream", f"http {status}")
        out = list(tcs.values())
        return "".join(text_parts), out or None, usage, None


def _msg_text(content):
    """OpenAI content -> plain text. Multipart lists join text parts;
    non-text parts are dropped (never str()-repr'd into the request)."""
    if isinstance(content, list):
        return "".join(p.get("text", "") for p in content
                       if isinstance(p, dict))
    return str(content or "")


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


def _usage_block(prompt, text, real=None):
    """OpenAI usage object: real ACP counters when present, else the
    documented ~4ch/tok estimate."""
    return real or {
        "prompt_tokens": _est_tokens(prompt),
        "completion_tokens": _est_tokens(text),
        "total_tokens": _est_tokens(prompt) + _est_tokens(text)}


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
        internal = getattr(sv, "internal", None)
        if internal:
            return self._internal(sv, internal, req, messages, model, cid)
        if getattr(sv, "acp", None):
            if req.get("stream"):
                want_usage = bool((req.get("stream_options") or {})
                                  .get("include_usage"))
                return self._sse_acp(sv, prompt, model, cid, want_usage)
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
            want_usage = bool((req.get("stream_options") or {})
                              .get("include_usage"))
            self._sse_head()
            line = "data: " + json.dumps(_chunk(text, model, cid)) + "\n\n"
            self.wfile.write(line.encode("utf-8"))
            self._sse_tail(model, cid,
                           _usage_block(prompt, text, usage)
                           if want_usage else None)
            return
        self._json(200, _completion(
            text, model, cid, prompt=prompt, usage=usage,
            ignored=[k for k in _UNSUPPORTED if k in req]))

    def _internal(self, sv, internal, req, messages, model, cid):
        """internal backend: raw inference with tool_calls round-trip."""
        tools = req.get("tools")
        model_uid = model if model != "devin" else None
        if req.get("stream"):
            want_usage = bool((req.get("stream_options") or {})
                              .get("include_usage"))
            deltas, err_box = [], [None]

            def feed(kind, obj):
                if kind == "text":
                    deltas.append(obj)
                    line = "data: " + json.dumps(
                        _chunk(obj, model, cid)) + "\n\n"
                else:  # tool_call
                    ch = _chunk("", model, cid)
                    ch["choices"][0]["delta"] = {"tool_calls": [
                        {"index": 0, **obj}]}
                    line = "data: " + json.dumps(ch) + "\n\n"
                self.wfile.write(line.encode("utf-8"))
                self.wfile.flush()
            with sv.sem:
                self._sse_head()
                text, tcs, usage, err_box[0] = internal.prompt(
                    messages, tools, model_uid, on_delta=feed)
            if err_box[0]:
                kind, msg = err_box[0]
                self.wfile.write(("data: " + json.dumps(
                    {"error": {"message": msg, "type": kind + "_error"}})
                    + "\n\n").encode("utf-8"))
            tail = _chunk("", model, cid)
            tail["choices"][0]["finish_reason"] = \
                "tool_calls" if tcs else "stop"
            tail["choices"][0]["delta"] = {}
            self.wfile.write(("data: " + json.dumps(tail) + "\n\n")
                             .encode("utf-8"))
            if want_usage:
                u = _chunk("", model, cid)
                u["choices"] = []
                u["usage"] = usage or _usage_block(
                    json.dumps(messages), "".join(deltas))
                self.wfile.write(("data: " + json.dumps(u) + "\n\n")
                                 .encode("utf-8"))
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return
        with sv.sem:
            text, tcs, usage, err = internal.prompt(
                messages, tools, model_uid)
        if err:
            kind, msg = err
            code = 504 if kind == "timeout" else 502
            return self._json(code, {"error": {"message": msg,
                                               "type": kind + "_error"}})
        out = _completion(text, model, cid, usage=usage,
                          prompt=json.dumps(messages))
        if tcs:
            m_ = out["choices"][0]["message"]
            m_["tool_calls"] = tcs
            m_["content"] = m_["content"] or ""
            out["choices"][0]["finish_reason"] = "tool_calls"
        ignored = [k for k in _UNSUPPORTED if k in req and k != "tools"]
        if ignored:
            out["x-ignored-params"] = ignored
        return self._json(200, out)

    def _sse_head(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

    def _sse_tail(self, model, cid, usage=None):
        end = _chunk("", model, cid)
        end["choices"][0]["finish_reason"] = "stop"
        end["choices"][0]["delta"] = {}
        tail = "data: " + json.dumps(end) + "\n\n"
        if usage is not None:
            # stream_options.include_usage contract: a final chunk with
            # empty choices carrying the usage block
            u = _chunk("", model, cid)
            u["choices"] = []
            u["usage"] = usage
            tail += "data: " + json.dumps(u) + "\n\n"
        self.wfile.write((tail + "data: [DONE]\n\n").encode("utf-8"))
        self.wfile.flush()

    def _sse_acp(self, sv, prompt, model, cid, want_usage):
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
            _, usage, err_box[0] = sv.acp.prompt(prompt, on_delta=feed)
        if err_box[0]:
            kind, msg = err_box[0]
            self.wfile.write(("data: " + json.dumps(
                {"error": {"message": msg, "type": kind + "_error"}})
                + "\n\n").encode("utf-8"))
        self._sse_tail(model, cid,
                       _usage_block(prompt, "".join(deltas), usage)
                       if want_usage else None)


def _opencode_block(port, model, token):
    return {"provider": {"devin-local": {
        "npm": "@ai-sdk/openai-compatible",
        "name": "Devin (local bridge)",
        "options": {"baseURL": f"http://127.0.0.1:{port}/v1",
                    "apiKey": token or ""},
        "models": {model or "devin": {"name": "devin"}}}}}


def _codex_block(port, model):
    return (f'model_provider = "devin-local"\n'
            f'model = "{model or "devin"}"\n\n'
            '[model_providers.devin-local]\n'
            'name = "Devin (local bridge)"\n'
            f'base_url = "http://127.0.0.1:{port}/v1"\n'
            'env_key = "DEVIN_LOCAL_API_KEY"\n'
            'wire_api = "chat"')


def setup(args):
    """Print harness config stanzas; --write merges opencode.json (#492)."""
    port = getattr(args, "port", 8787)
    if args.harness in ("hermes", "generic", "env"):
        tok = args.token or "<token-if-LAN>"
        print(f'export OPENAI_BASE_URL="http://127.0.0.1:{port}/v1"\n'
              f'export OPENAI_API_KEY="{tok}"\n'
              f'# model id: devin (or any id from GET /v1/models)\n'
              '# aider: OPENAI_API_BASE instead of OPENAI_BASE_URL')
        return
    if args.harness == "codex":
        print(_codex_block(port, args.model)
              + "\n# append into ~/.codex/config.toml; LAN token goes in "
              "DEVIN_LOCAL_API_KEY env")
        return
    block = _opencode_block(port, args.model, args.token)
    out = json.dumps(block, indent=2)
    if not args.write:
        print(out + "\n# merge into opencode.json "
              "(project) or ~/.config/opencode/opencode.json (global)")
        return
    path = args.write
    if os.path.exists(path):
        cfg = json.load(open(path, encoding="utf-8"))
        if (cfg.get("provider") or {}).get("devin-local"):
            sys.exit(f"{path} already has provider.devin-local — "
                     "refusing to clobber")
    else:
        cfg = {}
    cfg.setdefault("provider", {}).update(
        block["provider"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    print(f"merged provider.devin-local into {path}")


def doctor(args):
    """One-shot backend sanity: binary, model inventory, port (#492)."""
    devin = _devin_path(args.devin)
    port = getattr(args, "port", 8787)
    checks = {"devin": os.path.isfile(devin)
              or shutil.which(devin) is not None}
    models = _list_models(devin, tempfile.gettempdir()) \
        if checks["devin"] else []
    checks["models"] = len(models)
    import socket
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        checks["port_free"] = True
    except OSError:
        checks["port_free"] = False
    finally:
        s.close()
    # informational: does `devin acp` answer initialize? (the --backend
    # acp path). ~2-4s spawn; not part of `ok` — cli backend is default.
    if checks["devin"]:
        try:
            b = AcpBackend(devin, tempfile.gettempdir(), 15)
            b._spawn()
            checks["acp"] = b._proc.poll() is None
            b._proc.terminate()
        except (OSError, subprocess.SubprocessError):
            checks["acp"] = False
    ok = checks["devin"] and checks["models"] and checks["port_free"]
    print(_dumps({"ok": ok, **checks,
                      "verdict": ("ready" if ok else "fix above")}))
    sys.exit(0 if ok else 1)


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
    httpd.internal = None
    if args.backend == "internal":
        key, base = _credentials()
        if not key:
            sys.exit("internal backend needs windsurf_api_key in "
                     "credentials.toml or DEVIN_API_TOKEN env")
        httpd.internal = InternalBackend(key, base, timeout=args.timeout)
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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
    sv.add_argument("--backend", choices=("cli", "acp", "internal"),
                    default="cli",
                    help="cli=`devin -p` per request; acp=warm ACP "
                         "process — real incremental streaming + real "
                         "token usage (#489); internal=direct Connect "
                         "endpoint — real tool_calls round-trip "
                         "(undocumented, INTERNAL-PROTOCOL.md)")
    md = sub.add_parser("models")
    md.add_argument("--devin")
    st = sub.add_parser("setup")
    st.add_argument("harness", choices=("opencode", "hermes", "generic",
                                       "env", "codex"))
    st.add_argument("--write", metavar="PATH",
                    help="merge provider block into this opencode.json")
    st.add_argument("--model")
    st.add_argument("--token")
    st.add_argument("--port", type=int, default=8787)
    dr = sub.add_parser("doctor")
    dr.add_argument("--devin")
    dr.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    if args.cmd == "setup":
        setup(args)
    elif args.cmd == "doctor":
        doctor(args)
    elif args.cmd == "models":
        devin = _devin_path(args.devin)
        print(_dumps({"ok": True, "models": _list_models(
            devin, tempfile.gettempdir())}))
    else:
        serve(args)


if __name__ == "__main__":
    main()
