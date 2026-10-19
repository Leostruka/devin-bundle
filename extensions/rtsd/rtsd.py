#!/usr/bin/env python3
"""rtsd - RTS overlay daemon for the Devin bundle.

Local state daemon: ingests hook events, projects fleet/task/decision state
from .devin files plus an event-sourced v2 world (units/buildings/resources/
quests/map, world.py), serves snapshot+upserts over HTTP+WebSocket and the
web UI. A 2s tick recomputes time-derived state (heartbeat decay, idle,
minion TTL) and broadcasts deltas; replaying events.jsonl reproduces the
same world.

Endpoints (127.0.0.1 only):
  POST /event        append JSON event to .devin/rts/events.jsonl, broadcast
  GET  /snapshot     current projected state JSON
  GET  /health       {"ok": true}
  GET  /decisions    pending decisions list
  POST /decisions/<id>/answer  {"choice": ..., "text": ...} -> writes response file
  POST /intent       {"kind": "spawn|message|goal", ...} -> .devin/rts/intents/
  GET  /ws           WebSocket upgrade: hello -> snapshot, then upserts
  GET  /             web UI (web/index.html)

Stdlib only (bundle rule: no new deps). WS = minimal RFC 6455 implementation.
State root: <cwd>/.devin/rts/ unless --root is given.
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
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as worldmod  # noqa: E402

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_PORT = 8797
TICK_S = 2.0
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def safe_name(s):
    return bool(SAFE_NAME.match(s or "")) and ".." not in s \
        and bool(str(s).lstrip("."))

STATE = {"root": None, "clients": [], "lock": threading.Lock(),
        "write_lock": threading.Lock(), "token": None, "world": None}


def state_dir():
    d = os.path.join(STATE["root"], ".devin", "rts")
    for sub in ("", "decisions", "intents", "agents"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d


def append_event(ev):
    ev.setdefault("ts", time.time())
    path = os.path.join(state_dir(), "events.jsonl")
    with STATE["write_lock"]:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        project_fleet(ev)
        if STATE["world"] is not None:
            STATE["world"].apply(ev)
    broadcast({"type": "upsert", "event": ev})


def _find_agent_id(resp):
    if isinstance(resp, dict):
        for k in ("agent_id", "id"):
            if k in resp:
                return str(resp[k])
        resp = json.dumps(resp)
    if isinstance(resp, str):
        m = re.search(r"agent_id[=:\s]+([0-9a-fA-F-]{6,})", resp)
        if m:
            return m.group(1)
    return None


def _resp_text(resp):
    if isinstance(resp, dict):
        resp = json.dumps(resp)
    return resp if isinstance(resp, str) else ""


def _default_model():
    cfg = read_json(os.path.join(STATE["root"], "data", "bundle-models.json"), {})
    return cfg.get("default_subagent_model", "swe-2-max")


def project_fleet(ev):
    """Project hook events into .devin/rts/fleet.json (single writer: rtsd)."""
    if ev.get("type") != "hook.posttooluse":
        return
    tool = ev.get("tool")
    payload = ev.get("payload") or {}
    ti = payload.get("tool_input") or {}
    resp = payload.get("tool_response", payload.get("result"))
    fleet_path = os.path.join(state_dir(), "fleet.json")
    fleet = read_json(fleet_path, {})
    changed = False
    if tool == "run_subagent":
        aid = _find_agent_id(resp) or "fg-%d" % int(ev["ts"] * 1000)
        running = bool(ti.get("is_background"))
        fleet[aid] = {
            "id": aid,
            "profile": ti.get("profile", "?"),
            "title": ti.get("title", ""),
            "task": (ti.get("task") or "")[:120],
            "model": _default_model(),
            "status": "running" if running else "done",
            "spawned_at": ev["ts"],
            "lane": ti.get("lane", ""),
        }
        changed = True
    elif tool == "read_subagent":
        aid = str(ti.get("agent_id", ""))
        if aid and aid in fleet:
            txt = _resp_text(resp)
            if "completed successfully" in txt or '"done"' in txt:
                fleet[aid]["status"] = "done"
            elif "failed" in txt.lower() or "error" in txt.lower():
                fleet[aid]["status"] = "failed"
            changed = True
    if changed:
        with open(fleet_path, "w", encoding="utf-8") as f:
            json.dump(fleet, f, ensure_ascii=False, indent=2)


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def scan_issues(root):
    return worldmod.scan_issues(root)


def scan_ledgers(root):
    """Parse .devin/ledgers/*.md into gate state lists.

    Checkbox convention: [x]=pass, [ ]=pending, [!]/[F]=fail.
    Indented CHECK/EXPECT/EVIDENCE lines attach to the last gate.
    """
    return worldmod.scan_ledgers(root)


def build_snapshot():
    root = STATE["root"]
    rts = state_dir()
    fleet = read_json(os.path.join(rts, "fleet.json"), {})
    decisions = []
    ddir = os.path.join(rts, "decisions")
    for fn in sorted(os.listdir(ddir)):
        d = read_json(os.path.join(ddir, fn), None)
        if d and d.get("status") == "pending":
            decisions.append(d)
    intents = []
    idir = os.path.join(rts, "intents")
    for fn in sorted(os.listdir(idir)):
        d = read_json(os.path.join(idir, fn), None)
        if d and d.get("status") == "pending":
            intents.append(d)
    agents = dict(fleet)
    adir = os.path.join(rts, "agents")
    for key in os.listdir(adir):
        hb = read_json(os.path.join(adir, key, "status.json"), None)
        if not hb:
            continue
        hb["dir"] = key
        if key in agents:
            agents[key]["heartbeat"] = hb
            continue
        # heartbeat keyed by contract/handle id: attach to the agent
        # whose dispatch text references it
        for a in agents.values():
            if key in (a.get("task") or "") or key in (a.get("title") or ""):
                a["heartbeat"] = hb
                break
    ledgers = scan_ledgers(root)
    ledger_ids = {l["id"] for l in ledgers}
    fail_ledgers = {l["id"] for l in ledgers
                    if any(g["state"] == "fail" for g in l["gates"])}
    tasks = scan_issues(root)
    for t in tasks:
        if t["effort"] in ledger_ids:
            t["ledger"] = t["effort"]
    for a in agents.values():
        if a.get("lane") in ledger_ids:
            a["ledger"] = a["lane"]
        if a.get("lane") in fail_ledgers:
            a["gate_fail"] = True
    snap = {
        "generated_at": time.time(),
        "agents": list(agents.values()),
        "tasks": tasks,
        "decisions": decisions,
        "intents": intents,
        "ledgers": ledgers,
    }
    if STATE["world"] is not None:
        snap["v"] = 2
        snap["world"] = STATE["world"].snapshot(snap["generated_at"])
    return snap


# --- minimal WebSocket (RFC 6455, text frames only) ---

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


class Handler(BaseHTTPRequestHandler):
    server_version = "rtsd/0.1"

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
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", name)
        if not os.path.isfile(p):
            return None
        with open(p, "rb") as f:
            return f.read()

    def _auth(self):
        """Non-loopback clients need the session token (query/header)."""
        ip = self.client_address[0]
        if ip in ("127.0.0.1", "::1", "localhost") or not STATE["token"]:
            return True
        q = urllib.parse.parse_qs(
            urllib.parse.urlsplit(self.path).query)
        tok = (q.get("token", [None])[0]
               or self.headers.get("X-RTS-Token")
               or (self.headers.get("Authorization", "")
                   .removeprefix("Bearer ") or None))
        if tok and secrets.compare_digest(tok, STATE["token"]):
            append_event({"type": "auth.allow", "ip": ip, "ts": time.time()})
            return True
        append_event({"type": "auth.deny", "ip": ip,
                      "path": self.path.split("?")[0], "ts": time.time()})
        self._json(401, {"error": "auth required"})
        return False

    def do_GET(self):
        if not self._auth():
            return
        path = self.path.split("?")[0]
        if path == "/ws" and "upgrade" in self.headers.get("Connection", "").lower():
            return self._ws()
        if path == "/health":
            return self._json(200, {"ok": True})
        if path == "/snapshot":
            return self._json(200, build_snapshot())
        if path == "/decisions":
            return self._json(200, build_snapshot()["decisions"])
        static = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/index.html": ("index.html", "text/html; charset=utf-8"),
                  "/manifest.webmanifest": ("manifest.webmanifest",
                                            "application/manifest+json"),
                  "/sw.js": ("sw.js", "text/javascript; charset=utf-8")}
        if path in static:
            name, ctype = static[path]
            body = self._static(name)
            if body is None:
                return self._json(404, {"error": "ui not built"})
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
        if path == "/event":
            ev = self._body()
            if not isinstance(ev, dict) or not ev:
                return self._json(400, {"error": "bad event"})
            append_event(ev)
            return self._json(200, {"ok": True})
        if path == "/intent":
            it = self._body()
            kind = it.get("kind")
            if kind not in ("spawn", "message", "goal", "answer"):
                return self._json(400, {"error": "bad intent kind"})
            iid = str(it.setdefault("id", "i%d" % int(time.time() * 1000)))
            if not safe_name(iid):
                return self._json(400, {"error": "bad intent id"})
            it["status"] = "pending"
            p = os.path.join(state_dir(), "intents", iid + ".json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(it, f, ensure_ascii=False, indent=2)
            append_event({"type": "intent.created", "intent": it})
            return self._json(200, {"ok": True})
        m = re.match(r"^/decisions/([A-Za-z0-9_.-]+)/answer$", path)
        if m:
            dfile = os.path.join(state_dir(), "decisions", m.group(1) + ".json")
            d = read_json(dfile, None)
            if not d:
                return self._json(404, {"error": "unknown decision"})
            if d.get("status") == "answered":
                return self._json(409, {"error": "already answered"})
            ans = self._body()
            opts = d.get("options", [])
            choice = ans.get("choice")
            if opts and (not isinstance(choice, int)
                         or not 0 <= choice < len(opts)):
                return self._json(400, {"error": "choice out of range"})
            d["status"] = "answered"
            d["answer"] = ans
            d["answered_at"] = time.time()
            with open(dfile, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            with open(dfile + ".response", "w", encoding="utf-8") as f:
                json.dump(ans, f, ensure_ascii=False)
            append_event({"type": "decision.answered", "id": m.group(1)})
            return self._json(200, {"ok": True})
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
        with STATE["lock"]:
            STATE["clients"].append(sock)
        try:
            ws_send(sock, json.dumps(
                {"type": "snapshot", "snapshot": build_snapshot()},
                ensure_ascii=False))
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
        finally:
            with STATE["lock"]:
                if sock in STATE["clients"]:
                    STATE["clients"].remove(sock)
        self.close_connection = True


class RtsServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR allows stealing a live listener; forbid it so a
    # second rtsd on the same port fails loudly instead of splitting traffic.
    allow_reuse_address = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--remote", type=float, default=0, metavar="MIN",
                    help="open a LAN listener on port+1 for MIN minutes "
                         "with a per-session token, then deny-safe close")
    args = ap.parse_args()
    STATE["root"] = os.path.abspath(args.root)
    state_dir()
    STATE["world"] = worldmod.World.replay_file(
        STATE["root"], os.path.join(state_dir(), "events.jsonl"))
    srv = RtsServer(("127.0.0.1", args.port), Handler)
    srv.daemon_threads = True
    print("rtsd on http://127.0.0.1:%d (root=%s)" % (args.port, STATE["root"]))
    if args.remote > 0:
        STATE["token"] = secrets.token_urlsafe(16)
        rport = args.port + 1
        rsrv = RtsServer(("0.0.0.0", rport), Handler)
        rsrv.daemon_threads = True
        ttl = args.remote * 60

        def remote_serve():
            t = threading.Thread(target=rsrv.serve_forever, daemon=True)
            t.start()
            append_event({"type": "remote.open", "port": rport,
                          "ttl_s": ttl, "ts": time.time()})
            time.sleep(ttl)
            rsrv.shutdown()
            rsrv.server_close()
            STATE["token"] = None
            append_event({"type": "remote.expired", "port": rport,
                          "ts": time.time()})

        threading.Thread(target=remote_serve, daemon=True).start()
        print("remote: http://<lan-ip>:%d/?token=%s (ttl %ds)"
              % (rport, STATE["token"], int(ttl)))

    def tick_loop():
        while True:
            time.sleep(TICK_S)
            try:
                deltas = STATE["world"].tick(time.time())
                if deltas:
                    broadcast({"type": "tick", "ts": time.time(),
                               "deltas": deltas})
            except Exception:
                pass  # fail-open: a bad tick never kills the daemon

    threading.Thread(target=tick_loop, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
