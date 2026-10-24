#!/usr/bin/env python3
"""agent-rts server - DevinCraft/DevTycoon orchestration daemon (v3).

Sibling of rtsd: same .devin/rts/ state root, same event-sourced world
(imported via world_bridge), same intent/decision file queues, plus the
repository telemetry collectors the 3D client needs (git/gh/bundle).

Endpoints (127.0.0.1 only):
  POST /event        append JSON event to .devin/rts/events.jsonl, broadcast
  GET  /snapshot     {world, repo, decisions, intents}
  GET  /telemetry    collectors-only payload (the repo.* block)
  GET  /health       {"ok": true}
  GET  /decisions    pending decisions list
  POST /decisions/<id>/answer  {"choice": ..., "text": ...}
  POST /intent       {"kind": "spawn|message|goal|answer|order", ...}
  POST /cmd          allowlisted controls (forge_ticket, laya_guard,
                     compact_hint, refresh_repo)
  GET  /score        victory aggregates (delegates to world.score)
  GET  /buildings/<id>  building detail
  GET  /ws           WebSocket: hello -> snapshot -> delta/fx/alert frames
  GET  /             web UI (web/index.html)

Inbound WS frames: order (writes intent file), gate_answer (writes a
decision response), cmd (allowlist), set (shared prefs), ping, snapshot.

Stdlib only. State root: <cwd>/.devin/rts/ unless --root is given.
The game observes and relays; it never dispatches (GDD canon).
"""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world_bridge          # noqa: E402
import collectors            # noqa: E402

worldmod = world_bridge.worldmod

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_PORT = 8798
TICK_S = 2.0
REPO_TICK_S = 10.0
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
GAS_WARN_PCT = 10.0
GAS_CLEAR_PCT = 15.0

STATE = {"root": None, "clients": [], "lock": threading.Lock(),
         "write_lock": threading.RLock(), "token": None, "world": None,
         "spectator_token": None, "replay": None, "prefs": {},
         "log_offset": 0, "gas_alert": False, "stale_alerted": set(),
         "role_by_sock": {}}


def safe_name(s):
    return bool(SAFE_NAME.match(s or "")) and ".." not in s \
        and bool(str(s).lstrip("."))


def state_dir():
    return world_bridge.state_dir(STATE["root"])


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_prefs():
    d = read_json(os.path.join(state_dir(), "prefs.json"), {})
    return d if isinstance(d, dict) else {}


def save_prefs():
    try:
        p = os.path.join(state_dir(), "prefs.json")
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(STATE["prefs"], f, ensure_ascii=False)
        os.replace(tmp, p)
    except Exception:
        pass


def load_events(path):
    evs = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        evs.append(json.loads(ln))
                    except Exception:
                        pass
    except OSError:
        pass
    return evs


# ---- events / world ----

def append_event(ev):
    """The only path that mutates the log + world (rtsd parity)."""
    if STATE["replay"] is not None:
        return
    ev.setdefault("ts", time.time())
    path = os.path.join(state_dir(), world_bridge.EVENTS)
    with STATE["write_lock"]:
        data = json.dumps(ev, ensure_ascii=False).encode() + b"\n"
        with open(path, "ab") as f:
            f.write(data)
        STATE["log_offset"] += len(data)
        line = hint = None
        if STATE["world"] is not None:
            line = STATE["world"].apply(ev)
            try:
                hint = STATE["world"].event_hint(ev)
            except Exception:
                hint = None
    broadcast({"type": "upsert", "event": ev, "hint": hint, "feed": line})
    for fx in fx_for_event(ev):
        broadcast(fx)
    if ev.get("type") == "hook.permissionrequest":
        _permission_decision(ev)
    if ev.get("type") == "decision.created":
        p = ev.get("payload") or {}
        broadcast({"type": "decision", "op": "created", "id": p.get("id"),
                   "prompt": p.get("prompt"), "options": p.get("options"),
                   "timeout": 120})
    if ev.get("type") == "decision.answered":
        broadcast({"type": "decision", "op": "answered",
                   "id": ev.get("id")})


def fx_for_event(ev):
    """Map a real event to transient particle frames (GDD 1.4)."""
    out = []
    et = ev.get("type", "")
    if et == "hook.posttooluse":
        payload = ev.get("payload") or {}
        tool = ev.get("tool") or payload.get("tool_name") or ""
        resp = payload.get("tool_response") or {}
        failed = isinstance(resp, dict) and resp.get("success") is False
        bid = worldmod.TOOL_TO_BUILDING.get(tool, "town-hall")
        color = "red" if failed else _tool_color(tool)
        xy = _unit_xy(ev) or _building_xy(bid)
        out.append({"type": "fx", "fx": "bubble", "color": color,
                    "x": xy[0], "y": xy[1],
                    "label": "+" + (tool or "tool")})
        if failed and _looks_like_test(payload):
            out.append({"type": "alert", "level": "warn",
                        "code": "tests_red",
                        "msg": "test/gate command failed",
                        "x": xy[0], "y": xy[1]})
    elif et == "decision.created":
        xy = _building_xy("watchtower")
        out.append({"type": "fx", "fx": "gate_flash",
                    "x": xy[0], "y": xy[1]})
    elif et == "intent.created":
        it = ev.get("intent") or {}
        if it.get("order") == "god_power":
            out.append({"type": "fx", "fx": "meteor",
                        "x": it.get("x", 36), "y": it.get("y", 27)})
    return out


def _tool_color(tool):
    if tool in ("write", "edit", "notebook_edit", "exec", "get_output",
                "write_to_process", "kill_shell"):
        return "green"
    if tool in ("skill", "todo_write", "ask_user_question"):
        return "blue"
    return "purple"  # read-family, search, web, mcp


def _looks_like_test(payload):
    cmd = str(((payload.get("tool_input") or {}).get("command")) or "")
    return any(k in cmd for k in ("pytest", "test", "lint", "audit.py"))


def _building_xy(bid):
    w = STATE["world"]
    if w is not None:
        s = getattr(w, "sites", {}).get(bid) or \
            getattr(w, "sites", {}).get("town-hall")
        if s:
            return list(s["xy"])
    return [36, 27]


def _unit_xy(ev):
    """Best-effort: position of the unit owning this event's lane."""
    w = STATE["world"]
    if w is None:
        return None
    sid = str(ev.get("session_id") or "")
    for u in getattr(w, "units", {}).values():
        if str(u.get("lane") or u.get("session_id") or "") == sid:
            pos = u.get("pos") or {}
            if "x" in pos and "y" in pos:
                return [pos["x"], pos["y"]]
    return None


def _permission_decision(ev):
    """PermissionRequest hook -> pending decision file (rtsd parity #129)."""
    payload = ev.get("payload") or {}
    tool = ev.get("tool") or payload.get("tool_name") or "?"
    ti = payload.get("tool_input") or {}
    opts = payload.get("options") or payload.get("choices") \
        or ["allow", "deny"]
    if not isinstance(opts, list) or not opts:
        opts = ["allow", "deny"]
    opts = [str(o) for o in opts]
    summary = ti.get("command") or ti.get("file_path") \
        or ti.get("prompt") or json.dumps(ti, ensure_ascii=False)[:120]
    ddir = state_dir()
    base = int(ev.get("ts", time.time()) * 1000)
    n = 0
    while os.path.isfile(os.path.join(ddir, "decisions",
                                      "d%d.json" % (base + n))):
        n += 1
    did = "d%d" % (base + n)
    d = {"id": did, "kind": "permission",
         "prompt": "%s: %s" % (tool, summary),
         "options": opts, "status": "pending",
         "created_at": ev.get("ts", time.time()),
         "timeout": payload.get("timeout", 120),
         "tool": str(tool),
         "requester": str(ev.get("session_id")
                          or ti.get("lane") or "")}
    with open(os.path.join(ddir, "decisions", did + ".json"), "w",
              encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    append_event({"type": "decision.created",
                  "payload": {"id": did, "kind": "permission",
                              "prompt": d["prompt"], "options": opts,
                              "requester": d["requester"]}})


def write_intent(it):
    """Validate + persist an intent file (rtsd /intent parity)."""
    kind = it.get("kind")
    if kind not in ("spawn", "message", "goal", "answer", "order"):
        return None, "bad intent kind"
    iid = str(it.setdefault("id", "i%d" % int(time.time() * 1000)))
    if not safe_name(iid):
        return None, "bad intent id"
    it["status"] = "pending"
    p = os.path.join(state_dir(), "intents", iid + ".json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(it, f, ensure_ascii=False, indent=2)
    append_event({"type": "intent.created", "intent": it})
    return it, None


def answer_decision(did, ans):
    if not safe_name(did):
        return 400, {"error": "bad id"}
    dfile = os.path.join(state_dir(), "decisions", did + ".json")
    d = read_json(dfile, None)
    if not d:
        return 404, {"error": "unknown decision"}
    if d.get("status") == "answered":
        return 409, {"error": "already answered"}
    opts = d.get("options", [])
    choice = ans.get("choice")
    if opts and (not isinstance(choice, int)
                 or not 0 <= choice < len(opts)):
        return 400, {"error": "choice out of range"}
    d["status"] = "answered"
    d["answer"] = ans
    d["answered_at"] = time.time()
    with open(dfile, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    with open(dfile + ".response", "w", encoding="utf-8") as f:
        json.dump(ans, f, ensure_ascii=False)
    append_event({"type": "decision.answered", "id": did})
    return 200, {"ok": True}


# ---- allowlisted commands (GDD D5) ----

def run_cmd(body):
    cmd = str(body.get("cmd") or "")
    root = STATE["root"]
    if cmd == "refresh_repo":
        collectors.bust()
        return 200, {"ok": True, "repo": collectors.telemetry(
            root, STATE["world"])}
    if cmd == "compact_hint":
        append_event({"type": "context.compact",
                      "msg": "compaction/handoff requested from HUD"})
        return 200, {"ok": True}
    if cmd == "forge_ticket":
        return _cmd_forge(root, body)
    if cmd == "laya_guard":
        return _cmd_laya(root, body)
    return 400, {"error": "unknown cmd"}


def _cmd_forge(root, body):
    """Drag a ticket onto the Forge: build a prompt-compiler spec from the
    issue and run prompt_compiler.py --draft -> optimized_ready.md."""
    n = body.get("issue")
    repo = collectors.telemetry(root, STATE["world"])
    issue = next((i for i in repo["issues"]
                  if str(i.get("n")) == str(n)), None)
    title = (issue or {}).get("title") or str(body.get("title") or n)
    spec = {"effort": str(body.get("effort") or "high"),
            "persona": str(body.get("persona") or "Staff Engineer"),
            "goal": "Resolve issue %s: %s" % (n, title),
            "context": "Issue %s from the order queue. Repo: %s." % (
                n, (repo.get("git") or {}).get("branch") or "unknown"),
            "acceptance": ["Issue %s resolved" % n,
                           "bundle gates green (audit.py + pytest)"],
            "in_scope": [str(title)],
            "out_scope": ["unrelated refactors"],
            "phases": ["Investigate the issue", "Implement the fix",
                       "Verify with the project's checks"]}
    spec_path = os.path.join(state_dir(), "forge-spec-%s.json" % n)
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    pc = os.path.join(root, "extensions", "ai-tools", "prompt_compiler.py")
    if not os.path.isfile(pc):
        return 500, {"error": "prompt_compiler.py not found"}
    try:
        p = subprocess.run([sys.executable, pc, "--draft", spec_path],
                           cwd=root, capture_output=True, text=True,
                           timeout=30)
        try:
            res = json.loads(p.stdout)
        except Exception:
            res = {"ok": p.returncode == 0, "stdout": p.stdout[-500:],
                   "stderr": p.stderr[-500:]}
        return (200 if res.get("ok") else 400), res
    except Exception as e:
        return 500, {"error": "forge run failed: %s" % e}


def _cmd_laya(root, body):
    """LayaGuard gate check: laya_cli predict --preset guard."""
    cli = os.path.join(root, "extensions", "laya-tools", "laya_cli.py")
    if not os.path.isfile(cli):
        return 500, {"error": "laya_cli.py not found"}
    state = body.get("state")
    if state is None:
        return 400, {"error": "missing state"}
    try:
        p = subprocess.run(
            [sys.executable, cli, "predict", "--state",
             json.dumps(state), "--preset", "guard"],
            cwd=root, capture_output=True, text=True, timeout=300)
        try:
            return 200, json.loads(p.stdout)
        except Exception:
            return 200, {"ok": p.returncode == 0,
                         "stdout": p.stdout[-500:],
                         "stderr": p.stderr[-500:],
                         "note": "first run downloads ~1GB of weights"}
    except subprocess.TimeoutExpired:
        return 504, {"error": "laya predict timed out (model download?)"}
    except Exception as e:
        return 500, {"error": "laya run failed: %s" % e}


# ---- snapshot ----

def build_snapshot():
    now = time.time()
    w = STATE["world"]
    return {"ts": now,
            "world": w.snapshot(now) if w is not None else {},
            "repo": collectors.telemetry(STATE["root"], w)
            if w is not None else {},
            "decisions": collectors.pending_decisions(STATE["root"]),
            "intents": collectors.recent_intents(STATE["root"]),
            "prefs": dict(STATE["prefs"])}


# ---- websocket (RFC 6455 minimal, rtsd-proven) ----

def ws_accept(key):
    return base64.b64encode(
        hashlib.sha1((key + WS_GUID).encode()).digest()).decode()


def ws_send(sock, payload):
    data = payload.encode() if isinstance(payload, str) else payload
    n = len(data)
    if n < 126:
        head = struct.pack("!BB", 0x81, n)
    elif n < 65536:
        head = struct.pack("!BBH", 0x81, 126, n)
    else:
        head = struct.pack("!BBQ", 0x81, 127, n)
    sock.sendall(head + data)


def ws_recv(sock):
    def read(n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        return buf
    head = read(2)
    if not head:
        return None
    op = head[0] & 0x0F
    ln = head[1] & 0x7F
    if ln == 126:
        ln = struct.unpack("!H", read(2))[0]
    elif ln == 127:
        ln = struct.unpack("!Q", read(8))[0]
    mask = read(4) if head[1] & 0x80 else None
    data = read(ln) if ln else b""
    if data is None:
        return None
    if mask:
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return op, data


def broadcast(msg):
    payload = json.dumps(msg, ensure_ascii=False)
    with STATE["lock"]:
        dead = []
        for c in STATE["clients"]:
            try:
                ws_send(c, payload)
            except OSError:
                dead.append(c)
        for c in dead:
            STATE["clients"].remove(c)


def handle_ws_msg(sock, role, msg):
    """Inbound WS protocol (GDD 2.2). Spectators are read-only."""
    t = msg.get("type")
    if t == "ping":
        ws_send(sock, json.dumps({"type": "pong"}))
        return
    if t == "snapshot":
        snap = build_snapshot()
        snap["client_role"] = role
        ws_send(sock, json.dumps(
            dict({"type": "snapshot"}, **snap), ensure_ascii=False))
        return
    if role == "spectator":
        ws_send(sock, json.dumps(
            {"type": "error", "error": "spectator read-only"}))
        return
    if t == "order":
        it = {"kind": "order"}
        for k in ("to", "order", "x", "y", "quest", "power", "queue",
                  "id", "path"):
            if k in msg:
                it[k] = msg[k]
        it.setdefault("to", "all")
        it.setdefault("order", "move")
        it, err = write_intent(it)
        ws_send(sock, json.dumps(
            {"type": "ack", "of": "order",
             "ok": err is None, "error": err,
             "id": (it or {}).get("id")}, ensure_ascii=False))
        return
    if t == "gate_answer":
        code, res = answer_decision(str(msg.get("id") or ""),
                                    {"choice": msg.get("choice"),
                                     "text": msg.get("text")})
        ws_send(sock, json.dumps(
            {"type": "ack", "of": "gate_answer", "ok": code == 200,
             "result": res}, ensure_ascii=False))
        return
    if t == "cmd":
        code, res = run_cmd(msg)
        ws_send(sock, json.dumps(
            {"type": "ack", "of": "cmd", "ok": code == 200,
             "cmd": msg.get("cmd"), "result": res}, ensure_ascii=False))
        return
    if t == "set":
        k, v = str(msg.get("key") or ""), msg.get("value")
        if k:
            STATE["prefs"][k] = v
            save_prefs()
            broadcast({"type": "prefs", "prefs": dict(STATE["prefs"])})
        return


# ---- http handler ----

class Handler(BaseHTTPRequestHandler):
    server_version = "agent-rts/0.1"

    def log_message(self, fmt, *args):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        ln = int(self.headers.get("Content-Length") or 0)
        if not ln:
            return {}
        try:
            return json.loads(self.rfile.read(ln))
        except Exception:
            return {}

    def _static(self, name):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "web")
        p = os.path.normpath(os.path.join(base, name))
        if not (p + os.sep).startswith(base + os.sep) and p != base:
            return None
        if not os.path.isfile(p):
            return None
        with open(p, "rb") as f:
            return f.read()

    _CTYPES = {".html": "text/html; charset=utf-8",
               ".js": "text/javascript; charset=utf-8",
               ".mjs": "text/javascript; charset=utf-8",
               ".css": "text/css; charset=utf-8",
               ".json": "application/json; charset=utf-8",
               ".webmanifest": "application/manifest+json",
               ".png": "image/png", ".svg": "image/svg+xml",
               ".glb": "model/gltf-binary",
               ".ico": "image/x-icon"}

    def _auth(self):
        """Loopback is free; other clients need the session token. The
        spectator token marks the connection read-only (rtsd parity)."""
        ip = self.client_address[0]
        self._role = "admin"
        q = urllib.parse.parse_qs(
            urllib.parse.urlsplit(self.path).query)
        tok = (q.get("token", [None])[0]
               or self.headers.get("X-RTS-Token")
               or (self.headers.get("Authorization", "")
                   .removeprefix("Bearer ") or None))
        if tok and STATE["spectator_token"] and \
                secrets.compare_digest(tok, STATE["spectator_token"]):
            self._role = "spectator"
            return True
        if ip in ("127.0.0.1", "::1", "localhost") or not STATE["token"]:
            return True
        if tok and secrets.compare_digest(tok, STATE["token"]):
            return True
        if STATE["replay"] is None:
            append_event({"type": "auth.deny", "ip": ip,
                          "path": self.path.split("?")[0],
                          "ts": time.time()})
        self._json(401, {"error": "auth required"})
        return False

    def do_GET(self):
        if not self._auth():
            return
        path = self.path.split("?")[0]
        if path == "/ws" and \
                "upgrade" in self.headers.get("Connection", "").lower():
            return self._ws()
        if path == "/health":
            return self._json(200, {"ok": True})
        if path == "/snapshot":
            snap = build_snapshot()
            snap["client_role"] = getattr(self, "_role", "admin")
            return self._json(200, snap)
        if path == "/telemetry":
            return self._json(200, collectors.telemetry(
                STATE["root"], STATE["world"]))
        if path == "/decisions":
            return self._json(200, collectors.pending_decisions(
                STATE["root"]))
        if path == "/score" and STATE.get("world") is not None:
            return self._json(200, STATE["world"].score())
        if path == "/replay":
            if STATE["replay"] is None:
                return self._json(404, {"error": "not in replay mode"})
            return self._json(200, replay_status())
        mb = re.match(r"^/buildings/([A-Za-z0-9_-]+)$", path)
        if mb and STATE.get("world") is not None:
            rts = state_dir()
            intents = collectors.recent_intents(STATE["root"], limit=200)
            decs = len(collectors.pending_decisions(STATE["root"]))
            det = STATE["world"].building_detail(
                mb.group(1), time.time(),
                {"intents": intents, "remote": STATE.get("remote"),
                 "decisions_pending": decs})
            if det is None:
                return self._json(404, {"error": "unknown building"})
            return self._json(200, det)
        name = "index.html" if path in ("/", "/index.html") else \
            path.lstrip("/")
        body = self._static(name)
        if body is not None:
            ext = os.path.splitext(name)[1].lower()
            ctype = self._CTYPES.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return
        path = self.path.split("?")[0]
        if getattr(self, "_role", "admin") == "spectator":
            return self._json(403, {"error": "spectator read-only"})
        if STATE["replay"] is not None:
            if path == "/replay":
                st = replay_control(self._body())
                if st is None:
                    return self._json(404, {"error": "not in replay mode"})
                return self._json(200, st)
            return self._json(403, {"error": "replay mode is read-only"})
        if path == "/event":
            ev = self._body()
            if not isinstance(ev, dict) or not ev:
                return self._json(400, {"error": "bad event"})
            append_event(ev)
            return self._json(200, {"ok": True})
        if path == "/intent":
            it, err = write_intent(self._body())
            if err:
                return self._json(400, {"error": err})
            return self._json(200, {"ok": True})
        if path == "/cmd":
            code, res = run_cmd(self._body() or {})
            return self._json(code, res)
        m = re.match(r"^/decisions/([A-Za-z0-9_.-]+)/answer$", path)
        if m:
            code, res = answer_decision(m.group(1), self._body())
            return self._json(code, res)
        self._json(404, {"error": "not found"})

    def _ws(self):
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            return self._json(400, {"error": "no ws key"})
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", ws_accept(key))
        self.end_headers()
        sock = self.request
        sock.settimeout(60)
        role = getattr(self, "_role", "admin")
        with STATE["lock"]:
            STATE["clients"].append(sock)
        try:
            ws_send(sock, json.dumps(
                {"type": "hello", "server": "agent-rts", "v": 1,
                 "token_required": bool(STATE["token"])},
                ensure_ascii=False))
            snap = build_snapshot()
            snap["client_role"] = role
            ws_send(sock, json.dumps(
                dict({"type": "snapshot"}, **snap), ensure_ascii=False))
            while True:
                try:
                    frame = ws_recv(sock)
                except (OSError, socket.timeout):
                    frame = None
                if frame is None:
                    break
                op, data = frame
                if op == 8:
                    break
                if op == 9:
                    try:
                        pong = struct.pack("!BB", 0x8A, len(data)) + data
                        sock.sendall(pong)
                    except OSError:
                        break
                    continue
                if op != 1:
                    continue
                try:
                    msg = json.loads(data.decode("utf-8"))
                except Exception:
                    continue
                try:
                    handle_ws_msg(sock, role, msg)
                except Exception:
                    try:
                        ws_send(sock, json.dumps(
                            {"type": "error",
                             "error": "msg handling failed"}))
                    except OSError:
                        break
        finally:
            with STATE["lock"]:
                if sock in STATE["clients"]:
                    STATE["clients"].remove(sock)
        self.close_connection = True


class RtsServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR allows stealing a live listener; forbid it so a
    # second daemon on the same port fails loudly (rtsd parity).
    allow_reuse_address = False


# ---- replay ----

def replay_status():
    r = STATE["replay"]
    return {"total": len(r["events"]), "index": r["idx"],
            "playing": r["playing"], "speed": r["speed"],
            "done": r["idx"] >= len(r["events"])}


def replay_control(body):
    r = STATE["replay"]
    if r is None:
        return None
    act = str(body.get("action") or "")
    if act == "play":
        r["playing"] = True
        r["deadline"] = time.time()
    elif act == "pause":
        r["playing"] = False
    elif act == "seek":
        idx = int(body.get("index", 0))
        idx = max(0, min(idx, len(r["events"])))
        w = worldmod.World(STATE["root"])
        for ev in r["events"][:idx]:
            w.apply(ev)
        STATE["world"] = w
        r["idx"] = idx
    elif act == "speed":
        r["speed"] = max(0.25, min(8.0, float(body.get("speed", 1))))
    return replay_status()


def replay_loop():
    r = STATE["replay"]
    while True:
        time.sleep(0.25)
        if not r["playing"] or r["idx"] >= len(r["events"]):
            continue
        now = time.time()
        if now < r["deadline"]:
            continue
        ev = r["events"][r["idx"]]
        r["idx"] += 1
        line = STATE["world"].apply(ev)
        broadcast({"type": "upsert", "event": ev, "feed": line})
        nxt = r["events"][r["idx"]] if r["idx"] < len(r["events"]) else None
        gap = (nxt.get("ts", ev.get("ts", now))
               - ev.get("ts", now)) if nxt else 1.0
        r["deadline"] = now + max(0.05, gap / r["speed"])


# ---- out-of-band surfaces (rtsd poll_comms parity) ----

def poll_comms():
    w = STATE["world"]
    root = STATE["root"]
    mroot = os.path.join(root, ".devin", "mailboxes")
    if os.path.isdir(mroot):
        for to in sorted(os.listdir(mroot)):
            ib = os.path.join(mroot, to, "inbox")
            if not os.path.isdir(ib):
                continue
            for fn in sorted(os.listdir(ib)):
                if not fn.endswith(".json"):
                    continue
                d = read_json(os.path.join(ib, fn), None)
                if not d or not d.get("id") or d["id"] in w.mail_seen:
                    continue
                append_event({"type": "mail.deposit", "mail": {
                    "id": str(d["id"]),
                    "from": str(d.get("from") or "?"),
                    "to": str(d.get("to") or to),
                    "kind": str(d.get("type") or "task"),
                    "preview": str(d.get("content") or "")[:80]}})
    ddir = os.path.join(root, ".devin", "rts", "decisions")
    if os.path.isdir(ddir):
        for fn in sorted(os.listdir(ddir)):
            if not fn.endswith(".json"):
                continue
            d = read_json(os.path.join(ddir, fn), None)
            if not d or d.get("status") != "pending":
                continue
            did = str(d.get("id") or fn[:-5])
            if did in w.dec_seen:
                continue
            append_event({"type": "decision.created", "payload": {
                "id": did, "kind": str(d.get("kind") or "decision"),
                "prompt": str(d.get("prompt") or "")[:120],
                "options": d.get("options") or [],
                "requester": str(d.get("requester") or "")}})
    adir = os.path.join(root, ".devin", "rts", "agents")
    if os.path.isdir(adir):
        for key in sorted(os.listdir(adir)):
            hb = read_json(os.path.join(adir, key, "status.json"), None)
            if not hb:
                continue
            note = hb.get("note")
            if note and w.notes.get(key) != note:
                append_event({"type": "agent.note", "agent": key,
                              "note": str(note)[:120]})


def repo_tick():
    """Telemetry broadcast + gas alert edge (10s cadence)."""
    repo = collectors.telemetry(STATE["root"], STATE["world"])
    broadcast({"type": "repo", "repo": repo})
    free = (repo.get("gas") or {}).get("free_pct")
    if free is not None:
        if free < GAS_WARN_PCT and not STATE["gas_alert"]:
            STATE["gas_alert"] = True
            broadcast({"type": "alert", "level": "crit",
                       "code": "context_low",
                       "msg": "context window %.0f%% free - compact or "
                              "hand off" % free})
        elif free > GAS_CLEAR_PCT:
            STATE["gas_alert"] = False
    for i in repo.get("issues") or []:
        if i.get("age_s", 0) > 14 * 86400 \
                and i.get("n") not in STATE["stale_alerted"]:
            STATE["stale_alerted"].add(i.get("n"))
            broadcast({"type": "alert", "level": "warn",
                       "code": "issue_stale",
                       "msg": "order %s aging %sd" % (
                           i.get("n"), int(i["age_s"] / 86400))})


def tail_loop():
    """Pick up events appended out-of-band (rts-emit fallback, rtsd)."""
    path = os.path.join(state_dir(), world_bridge.EVENTS)
    while True:
        time.sleep(0.5)
        try:
            with STATE["write_lock"]:
                evs, STATE["log_offset"] = world_bridge.tail_new(
                    STATE["world"], path, STATE["log_offset"])
            for ev in evs:
                broadcast({"type": "upsert", "event": ev,
                           "hint": None, "feed": None})
                for fx in fx_for_event(ev):
                    broadcast(fx)
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("AGENT_RTS_PORT",
                                               DEFAULT_PORT)))
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--replay", metavar="EVENTS.JSONL")
    ap.add_argument("--remote", type=float, default=0, metavar="MIN",
                    help="open a LAN listener on port+1 for MIN minutes")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    STATE["root"] = os.path.abspath(args.root)
    state_dir()
    STATE["prefs"] = load_prefs()
    if args.replay:
        events = load_events(os.path.abspath(args.replay))
        STATE["replay"] = {"path": os.path.abspath(args.replay),
                           "events": events, "idx": 0, "playing": False,
                           "speed": 1.0, "deadline": 0}
        STATE["world"] = worldmod.World(STATE["root"])
        threading.Thread(target=replay_loop, daemon=True).start()
    else:
        STATE["world"], STATE["log_offset"] = world_bridge.open_world(
            STATE["root"])
        threading.Thread(target=tail_loop, daemon=True).start()
    srv = RtsServer(("127.0.0.1", args.port), Handler)
    srv.daemon_threads = True
    url = "http://127.0.0.1:%d" % args.port
    print("agent-rts on %s (root=%s%s)" % (
        url, STATE["root"],
        ", replay=%s" % args.replay if args.replay else ""))
    if args.remote > 0:
        STATE["token"] = secrets.token_urlsafe(16)
        STATE["spectator_token"] = secrets.token_urlsafe(16)
        rport = args.port + 1
        rsrv = RtsServer(("0.0.0.0", rport), Handler)
        rsrv.daemon_threads = True
        threading.Thread(target=rsrv.serve_forever, daemon=True).start()
        with open(os.path.join(state_dir(), "remote.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"port": rport, "token": STATE["token"],
                       "spectator_token": STATE["spectator_token"],
                       "expires_at": time.time() + args.remote * 60},
                      f, indent=2)
        print("remote: http://<lan-ip>:%d/?token=%s (ttl %dm)"
              % (rport, STATE["token"], int(args.remote)))

    def tick_loop():
        last_repo = 0.0
        while True:
            time.sleep(TICK_S)
            try:
                if STATE["replay"] is None:
                    poll_comms()
                deltas = STATE["world"].tick(time.time())
                if deltas:
                    broadcast({"type": "tick", "ts": time.time(),
                               "deltas": deltas})
                if time.time() - last_repo > REPO_TICK_S:
                    last_repo = time.time()
                    repo_tick()
            except Exception:
                pass  # fail-open: a bad tick never kills the daemon

    threading.Thread(target=tick_loop, daemon=True).start()
    if not args.no_browser:
        try:
            import webbrowser
            threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
