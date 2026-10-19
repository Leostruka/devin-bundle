#!/usr/bin/env python3
"""Gate for ticket 01: start rtsd, POST /event, verify WS snapshot+upsert.

Usage: python extensions/rtsd/selftest.py [root]
Exits 0 + "ALL PASS" on success, 1 otherwise.
"""
import base64
import http.client
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time

PORT = 8871
HERE = os.path.dirname(os.path.abspath(__file__))


def ws_connect(port):
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        "GET /ws HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\n"
        "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n" % key)
    s.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)
    assert b"101" in buf.split(b"\r\n")[0], buf[:80]
    return s


def ws_read(s):
    head = s.recv(2)
    op, ln = head[0] & 0x0F, head[1] & 0x7F
    if ln == 126:
        ln = struct.unpack("!H", s.recv(2))[0]
    elif ln == 127:
        ln = struct.unpack("!Q", s.recv(8))[0]
    data = b""
    while len(data) < ln:
        data += s.recv(ln - len(data))
    return op, data.decode()


def post(port, path, obj):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("POST", path, json.dumps(obj), {"Content-Type": "application/json"})
    r = c.getresponse()
    r.read()
    return r.status


def get(port, path):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("GET", path)
    r = c.getresponse()
    return r.status, json.loads(r.read())


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    os.makedirs(os.path.join(root, ".devin"), exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "rtsd.py"),
         "--port", str(PORT), "--root", root],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                st, body = get(PORT, "/health")
                if st == 200 and body.get("ok"):
                    break
            except Exception:
                time.sleep(0.1)
        else:
            print("FAIL: daemon did not start")
            return 1

        st, snap = get(PORT, "/snapshot")
        assert st == 200 and "agents" in snap and "tasks" in snap, snap
        print("PASS snapshot keys:", sorted(snap.keys()))

        ws = ws_connect(PORT)
        op, data = ws_read(ws)
        hello = json.loads(data)
        assert hello["type"] == "snapshot" and "snapshot" in hello, hello
        print("PASS ws hello->snapshot")

        assert post(PORT, "/event", {"type": "test.ping", "n": 1}) == 200
        op, data = ws_read(ws)
        up = json.loads(data)
        assert up["type"] == "upsert" and up["event"]["type"] == "test.ping", up
        print("PASS ws upsert after POST /event")

        log = os.path.join(root, ".devin", "rts", "events.jsonl")
        assert os.path.isfile(log)
        lines = open(log, encoding="utf-8").read().strip().splitlines()
        assert any(json.loads(l)["type"] == "test.ping" for l in lines)
        print("PASS events.jsonl append (%d lines)" % len(lines))

        assert post(PORT, "/intent",
                    {"kind": "spawn", "profile": "researcher",
                     "task": "probe"}) == 200
        st, snap = get(PORT, "/snapshot")
        assert any(i.get("kind") == "spawn" for i in snap["intents"])
        print("PASS intent queued + in snapshot")

        # ticket 03: fleet projection from run_subagent hook events
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "run_subagent",
            "payload": {"tool_input": {"profile": "researcher",
                                       "task": "probe task",
                                       "is_background": True},
                        "tool_response": {"agent_id": "abc12345"}}})
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "read_subagent",
            "payload": {"tool_input": {"agent_id": "abc12345"},
                        "tool_response": "completed successfully"}})
        st, snap = get(PORT, "/snapshot")
        agents = {a["id"]: a for a in snap["agents"]}
        assert "abc12345" in agents, agents
        assert agents["abc12345"]["status"] == "done", agents["abc12345"]
        assert agents["abc12345"]["profile"] == "researcher"
        fl = json.load(open(os.path.join(
            root, ".devin", "rts", "fleet.json"), encoding="utf-8"))
        assert fl["abc12345"]["status"] == "done"
        print("PASS fleet spawned->done via hook events")

        # ticket 08: ledger projection (pass/fail/pending + hero gate_fail)
        ldir = os.path.join(root, ".devin", "ledgers")
        idir = os.path.join(root, ".devin", "scratch", "eff", "issues")
        os.makedirs(ldir, exist_ok=True)
        os.makedirs(idir, exist_ok=True)
        with open(os.path.join(ldir, "eff.md"), "w", encoding="utf-8") as f:
            f.write("# G\n\n- [x] G1: ok\n  CHECK: c\n  EXPECT: e\n  EVIDENCE: ev\n"
                    "- [!] G2: bad\n  CHECK: c2\n  EXPECT: e2\n  EVIDENCE: boom\n"
                    "- [ ] G3: todo\n  CHECK: -\n  EXPECT: -\n  EVIDENCE: pending\n")
        with open(os.path.join(idir, "01-t.md"), "w", encoding="utf-8") as f:
            f.write("# t\n\nStatus: needs-triage\nBlocked by: -\n")
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "run_subagent",
            "payload": {"tool_input": {"profile": "p", "task": "t",
                                       "is_background": True,
                                       "lane": "eff"},
                        "tool_response": {"agent_id": "lane1"}}})
        st, snap = get(PORT, "/snapshot")
        lg = {l["id"]: l for l in snap["ledgers"]}
        assert "eff" in lg, lg
        states = {g["id"]: g["state"] for g in lg["eff"]["gates"]}
        assert states == {"G1": "pass", "G2": "fail", "G3": "pending"}, states
        assert lg["eff"]["path"].endswith(os.path.join(
            ".devin", "ledgers", "eff.md"))
        ag = {a["id"]: a for a in snap["agents"]}
        assert ag["lane1"].get("gate_fail") is True, ag["lane1"]
        tk = {t["id"]: t for t in snap["tasks"]}
        assert tk["01-t"].get("ledger") == "eff", tk["01-t"]
        print("PASS ledger projection (pass/fail/pending + gate_fail)")

        # v3.8.0 #120: snapshot v2 world model
        st, snap = get(PORT, "/snapshot")
        assert snap.get("v") == 2 and isinstance(snap.get("world"), dict)
        w = snap["world"]
        for k in ("units", "buildings", "resources", "quests", "map"):
            assert k in w, list(w)
        assert any(b["id"] == "barracks" for b in w["buildings"])
        assert {q["id"] for q in w["quests"]} >= {"01-t"}
        units = {u["id"]: u for u in w["units"]}
        assert units["abc12345"]["kind"] == "hero"
        assert units["abc12345"]["cls"] == "Far Seer"  # researcher -> GDD
        assert units["abc12345"]["status"] == "done"
        assert units["lane1"]["status_live"] in ("running", "idle", "stale")
        assert w["resources"]["supply_used"] >= 0
        assert isinstance(w["map"]["regions"], list)
        print("PASS snapshot v2 (units/buildings/resources/quests/map)")

        # #120 tick: old heartbeat-less hero decays running -> idle -> stale
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "run_subagent",
            "ts": time.time() - 700,
            "payload": {"tool_input": {"profile": "implementer",
                                       "task": "old job",
                                       "is_background": True},
                        "tool_response": {"agent_id": "oldhero"}}})
        st, snap = get(PORT, "/snapshot")
        u = {x["id"]: x for x in snap["world"]["units"]}["oldhero"]
        assert u["status_live"] == "stale", u
        # minion from exec shell + kill_shell expiry
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "exec",
            "payload": {"tool_input": {"command": "sleep 30"},
                        "tool_response": {"shell_id": "zz9"}}})
        st, snap = get(PORT, "/snapshot")
        assert any(x.get("kind") == "minion" and x["id"] == "sh-zz9"
                   for x in snap["world"]["units"]), snap["world"]["units"]
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "kill_shell",
            "payload": {"tool_input": {"shell_id": "zz9"},
                        "tool_response": {}}})
        st, snap = get(PORT, "/snapshot")
        assert not any(x["id"] == "sh-zz9" for x in snap["world"]["units"])
        print("PASS tick decay + minion spawn/despawn")

        # #120 determinism: replaying events.jsonl rebuilds the same world
        sys.path.insert(0, HERE)
        import world as worldmod
        now = snap["world"]["now"]
        events = [json.loads(l) for l in
                  open(log, encoding="utf-8") if l.strip()]
        rw = worldmod.World.replay(root, events, now).snapshot(now)
        assert rw == snap["world"], "replay diverged from live world"
        print("PASS replay(events.jsonl) == live world (%d events)"
              % len(events))

        print("ALL PASS")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(3)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
