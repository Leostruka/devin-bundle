"""rtsd TUI - terminal client for the RTS overlay daemon (stdlib only).

Same protocol as the web UI: HTTP for state/commands, WS /ws for the live
feed. Line-oriented REPL plus --cmd for non-interactive use (test client).

Commands:
  /status              daemon health + snapshot counts
  /agents              fleet table
  /tasks               quest board (scratch issues)
  /decisions           pending decisions
  /answer <id> <idx>   answer a pending decision
  /intent <json>       POST an intent (spawn|message|goal|answer)
  /feed                live upsert feed via /ws (Ctrl+C to stop)
  /quit                exit

Usage:
  python tui.py [--host 127.0.0.1] [--port 8797] [--cmd "/agents"]
"""
import argparse
import base64
import json
import os
import re
import socket
import struct
import sys
import urllib.request
import urllib.error


def http(host, port, method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(
        "http://%s:%d%s" % (host, port, path), data=data,
        headers={"Content-Type": "application/json"}, method=method)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"error": "http %d" % e.code}
    except OSError as e:
        return {"error": str(e)}


def snapshot(host, port):
    return http(host, port, "GET", "/snapshot")


def cmd_status(h, p, _a):
    snap = snapshot(h, p)
    if "error" in snap and len(snap) == 1:
        return "daemon unreachable: %s" % snap["error"]
    return "agents=%d tasks=%d decisions=%d intents=%d" % (
        len(snap.get("agents", [])), len(snap.get("tasks", [])),
        len(snap.get("decisions", [])), len(snap.get("intents", [])))


def cmd_agents(h, p, _a):
    snap = snapshot(h, p)
    out = ["%-12s %-12s %-8s %s" % ("ID", "PROFILE", "STATUS", "TITLE")]
    for a in snap.get("agents", []):
        out.append("%-12s %-12s %-8s %s" % (
            a.get("id", "?")[:12], a.get("profile", "?")[:12],
            a.get("status", "?"), a.get("title", "")[:60]))
    return "\n".join(out)


def cmd_tasks(h, p, _a):
    snap = snapshot(h, p)
    out = ["%-24s %-14s %-10s %s" % ("ID", "EFFORT", "STATUS", "TITLE")]
    for t in snap.get("tasks", []):
        out.append("%-24s %-14s %-10s %s" % (
            t.get("id", "?")[:24], t.get("effort", "?")[:14],
            t.get("status", "?"), t.get("title", "")[:50]))
    return "\n".join(out)


def cmd_decisions(h, p, _a):
    ds = http(h, p, "GET", "/decisions")
    if not ds:
        return "no pending decisions"
    out = []
    for d in ds:
        opts = " | ".join("[%d] %s" % (i, o) for i, o in
                          enumerate(d.get("options", [])))
        out.append("%s %s :: %s" % (d.get("id", "?"), d.get("prompt", ""), opts))
    return "\n".join(out)


def cmd_answer(h, p, args):
    if len(args) < 2:
        return "usage: /answer <id> <choice-index> [text]"
    r = http(h, p, "POST", "/decisions/%s/answer" % args[0],
             {"choice": int(args[1]), "text": " ".join(args[2:])})
    return json.dumps(r)


def cmd_intent(h, p, args):
    if not args:
        return 'usage: /intent {"kind":"message","to":"x","text":"y"}'
    try:
        it = json.loads(" ".join(args))
    except ValueError:
        return "bad json"
    return json.dumps(http(h, p, "POST", "/intent", it))


def _ws_frame(op, data):
    """Client->server frame, masked per RFC 6455."""
    mask = os.urandom(4)
    n = len(data)
    if n < 126:
        head = struct.pack("!BB", 0x80 | op, 0x80 | n)
    elif n < 65536:
        head = struct.pack("!BBH", 0x80 | op, 0x80 | 126, n)
    else:
        head = struct.pack("!BBQ", 0x80 | op, 0x80 | 127, n)
    return head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data))


def ws_feed(host, port):
    s = socket.create_connection((host, port), timeout=10)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall((
        "GET /ws HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
        "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n" % (host, port, key)).encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = s.recv(4096)
        if not chunk:
            return "ws handshake failed"
        resp += chunk
    if b"101" not in resp.split(b"\r\n", 1)[0]:
        return "ws upgrade refused: " + resp.split(b"\r\n", 1)[0].decode(errors="replace")
    print("[feed] connected; Ctrl+C to stop", file=sys.stderr)
    s.settimeout(None)
    try:
        while True:
            head = s.recv(2)
            if not head:
                break
            op = head[0] & 0x0F
            ln = head[1] & 0x7F
            ext = {126: 2, 127: 8}.get(ln, 0)
            if ext:
                buf = b""
                while len(buf) < ext:
                    buf += s.recv(ext - len(buf))
                ln = struct.unpack("!H" if ext == 2 else "!Q", buf)[0]
            data = b""
            while len(data) < ln:
                data += s.recv(ln - len(data))
            if op == 8:
                break
            if op == 9:
                s.sendall(_ws_frame(0xA, data))
                continue
            if op == 1:
                try:
                    msg = json.loads(data)
                except ValueError:
                    continue
                t = msg.get("type", "?")
                if t == "snapshot":
                    ss = msg.get("snapshot", {})
                    nbr = len((ss.get("world") or {}).get("breaches", []))
                    print("[feed] snapshot: %d agents, %d tasks, "
                          "%d pending decisions, %d breaches" % (
                              len(ss.get("agents", [])),
                              len(ss.get("tasks", [])),
                              len(ss.get("decisions", [])), nbr))
                    for b in (ss.get("world") or {}).get("breaches", []):
                        print("[ALERT gate-fail] BREACH %s: ledger %s "
                              "gates %s" % (b.get("region"),
                                            b.get("ledger"),
                                            ",".join(b.get("gates", []))))
                else:
                    # #133 alert lines: council calls + gate fails print
                    # as first-class alerts, then the generic frame line
                    if t == "upsert":
                        ev = msg.get("event") or {}
                        hint = msg.get("hint") or {}
                        ln = msg.get("feed") or {}
                        if ev.get("type") == "decision.created":
                            pl = ev.get("payload") or {}
                            print("[ALERT decision] %s: %s" % (
                                pl.get("id", "?"),
                                pl.get("prompt") or pl.get("kind", "")))
                        if hint.get("kind") == "fail" or (
                                ln.get("kind") == "debrief" and
                                re.search(r"fail|retreat|unit down",
                                          ln.get("text") or "", re.I)):
                            print("[ALERT gate-fail] %s" % (
                                ln.get("text") or ev.get("tool") or ""))
                    print("[feed] %s %s" % (t, json.dumps(
                        {k: v for k, v in msg.items() if k != "type"},
                        ensure_ascii=False)[:160]))
    except KeyboardInterrupt:
        pass
    finally:
        try:
            s.sendall(_ws_frame(0x8, b""))
        except OSError:
            pass
        s.close()
    return "[feed] closed"


COMMANDS = {
    "/status": cmd_status,
    "/agents": cmd_agents,
    "/tasks": cmd_tasks,
    "/decisions": cmd_decisions,
    "/answer": cmd_answer,
    "/intent": cmd_intent,
}


def run_line(host, port, line):
    parts = line.strip().split()
    if not parts:
        return None
    cmd, args = parts[0].lower(), parts[1:]
    if cmd == "/feed":
        return ws_feed(host, port)
    if cmd in ("/quit", "/exit", "/help"):
        return "commands: " + " ".join(sorted(COMMANDS) + ["/feed", "/quit"])
    fn = COMMANDS.get(cmd)
    if not fn:
        return "unknown command (try /help)"
    try:
        return fn(host, port, args)
    except Exception as e:
        return "error: %s" % e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(
        os.environ.get("RTSD_PORT", "8797")))
    ap.add_argument("--cmd", action="append",
                    help="run command non-interactively (repeatable)")
    args = ap.parse_args()
    if args.cmd:
        rc = 0
        for c in args.cmd:
            out = run_line(args.host, args.port, c)
            if out is not None:
                print(out)
            if out and str(out).startswith("error"):
                rc = 1
        return rc
    print("rtsd tui - /help for commands")
    while True:
        try:
            line = input("rts> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        out = run_line(args.host, args.port, line)
        if line.strip().lower() in ("/quit", "/exit"):
            break
        if out is not None:
            print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
