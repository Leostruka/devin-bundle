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
  /score               victory screen: quests/gates/heroes/tokens
  /history             match history: past session logs + stats
  /replay              replay status (replay-mode daemon only)
  /play | /pause       replay playback control
  /speed <n>           replay speed (1, 2, 4...)
  /seek <index>        jump to event index (scrub)
  /feed                live upsert feed via /ws (Ctrl+C to stop)
  /quit                exit

Usage:
  python tui.py [--host 127.0.0.1] [--port 8797] [--cmd "/agents"]
  python tui.py --replay .devin/rts/events.jsonl   # console + playback
  python tui.py --spectate --token <t> --host <ip> --port <p>
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


TOKEN = None          # session or spectator token (X-RTS-Token)
SPECTATE = False      # --spectate: console blocks commands locally too;
                      # the daemon still enforces read-only server-side


def http(host, port, method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    hdrs = {"Content-Type": "application/json"}
    if TOKEN:
        hdrs["X-RTS-Token"] = TOKEN
    req = urllib.request.Request(
        "http://%s:%d%s" % (host, port, path), data=data,
        headers=hdrs, method=method)
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


def cmd_score(h, p, _a):
    sc = http(h, p, "GET", "/score")
    if "error" in sc and len(sc) == 1:
        return "score unavailable: %s" % sc["error"]
    out = ["== SCORE ==",
           "quests %d/%d  gates %d/%d pass (%d fail)  tokens %d  "
           "calls %d  duration %ds" % (
               sc["quests_done"], sc["quests_total"],
               sc["gates_pass"], sc["gates_total"], sc["gates_fail"],
               sc["gold"], sc["calls"], sc["duration_s"])]
    if sc.get("goal"):
        out.append("main quest: %s" % sc["goal"])
    for u in sc["heroes"][:8]:
        out.append("  %-12s %-14s lvl %-3d xp %-4d %s" % (
            u["id"][:12], (u.get("cls") or "?")[:14],
            u.get("level", 1), u.get("xp", 0), u.get("status") or "?"))
    return "\n".join(out)


def cmd_history(h, p, _a):
    ss = http(h, p, "GET", "/sessions")
    if isinstance(ss, dict):
        return "history unavailable: %s" % ss.get("error", "?")
    if not ss:
        return "no recorded sessions"
    out = ["%-28s %-6s %-8s %-7s %-7s %s" % (
        "LOG", "EVENTS", "AGENTS", "QUESTS", "TOKENS", "DUR")]
    for s in ss:
        out.append("%-28s %-6d %-8d %-7s %-7d %ds" % (
            s["id"][:28], s["events"], s["agents"],
            "%d/%d" % (s["quests_done"], s["quests_total"]),
            s["tokens"], s["duration_s"]))
    return "\n".join(out)


def cmd_replay(h, p, _a):
    r = http(h, p, "GET", "/replay")
    if "error" in r:
        return "replay: %s" % r["error"]
    return "replay %s %d/%d speed=%gx%s" % (
        os.path.basename(r["path"]), r["index"], r["total"],
        r["speed"], " [done]" if r["done"] else
        " playing" if r["playing"] else " paused")


def _replay_ctl(h, p, body):
    return json.dumps(http(h, p, "POST", "/replay", body))


def cmd_play(h, p, _a):
    return _replay_ctl(h, p, {"action": "play"})


def cmd_pause(h, p, _a):
    return _replay_ctl(h, p, {"action": "pause"})


def cmd_speed(h, p, args):
    if not args:
        return "usage: /speed <n>  (1x/2x/4x...)"
    try:
        return _replay_ctl(h, p, {"speed": float(args[0])})
    except ValueError:
        return "bad speed"


def cmd_seek(h, p, args):
    if not args:
        return "usage: /seek <event-index>"
    try:
        return _replay_ctl(h, p, {"action": "seek",
                                  "index": int(args[0])})
    except ValueError:
        return "bad index"


def cmd_answer(h, p, args):
    if SPECTATE:
        return "spectator console is read-only"
    if len(args) < 2:
        return "usage: /answer <id> <choice-index> [text]"
    r = http(h, p, "POST", "/decisions/%s/answer" % args[0],
             {"choice": int(args[1]), "text": " ".join(args[2:])})
    return json.dumps(r)


def cmd_intent(h, p, args):
    if SPECTATE:
        return "spectator console is read-only"
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
        "GET /ws%s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
        "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
        % ("?token=" + TOKEN if TOKEN else "",
           host, port, key)).encode())
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
    "/score": cmd_score,
    "/history": cmd_history,
    "/replay": cmd_replay,
    "/play": cmd_play,
    "/pause": cmd_pause,
    "/speed": cmd_speed,
    "/seek": cmd_seek,
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
    ap.add_argument("--token", default=os.environ.get("RTSD_TOKEN"),
                    help="session or spectator token (X-RTS-Token)")
    ap.add_argument("--spectate", action="store_true",
                    help="read-only console: /intent + /answer blocked "
                         "locally; the daemon enforces it server-side "
                         "for spectator tokens")
    ap.add_argument("--replay", metavar="EVENTS.JSONL",
                    help="spawn rtsd --replay on --port and connect the "
                         "console to it (/play /pause /speed /seek)")
    args = ap.parse_args()
    global TOKEN, SPECTATE
    TOKEN = args.token
    SPECTATE = bool(args.spectate)
    proc = None
    if args.replay:
        import subprocess
        here = os.path.dirname(os.path.abspath(__file__))
        proc = subprocess.Popen(
            [sys.executable, os.path.join(here, "rtsd.py"),
             "--port", str(args.port), "--root", os.getcwd(),
             "--replay", os.path.abspath(args.replay)])
        for _ in range(50):                     # wait for /health
            r = http(args.host, args.port, "GET", "/health")
            if r.get("ok"):
                break
            import time as _t
            _t.sleep(0.1)
        print("[replay] %s -> http://%s:%d" % (
            args.replay, args.host, args.port))
    try:
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
    finally:
        if proc is not None:
            proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
