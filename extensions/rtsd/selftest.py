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


def ws_drain(s, quiet=0.2):
    """Discard all buffered WS frames (upsert backlog from earlier posts)."""
    s.settimeout(quiet)
    try:
        while True:
            ws_read(s)
    except Exception:
        pass
    finally:
        s.settimeout(5)


def ws_until_hint(s, kinds, tries=8):
    """Read upserts until one carries a hint of the expected kind."""
    for _ in range(tries):
        op, data = ws_read(s)
        m = json.loads(data)
        h = m.get("hint")
        if m.get("type") == "upsert" and h and h.get("kind") in kinds:
            return h
    raise AssertionError("no hint of %s in %d frames" % (kinds, tries))


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
    for d in (".devin", "alpha", "beta"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    with open(os.path.join(root, "alpha", "f.py"), "w") as f:
        f.write("x = 1\n")
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

        # #122 world map: territories from top-level dirs, plots, fog, POIs
        m = w["map"]
        assert m["w"] == 72 and m["h"] == 54
        n = m["w"] * m["h"]
        assert len(m["tile_region"]) == n and len(m["fog"]) == n
        assert len(m["mark"]) == n
        rids = {r["id"] for r in m["regions"]}
        assert {"alpha", "beta", ".devin", "root"} <= rids, rids
        assert all(r["capital"] and len(r["plots"]) == 2
                   for r in m["regions"])
        assert os.path.isfile(os.path.join(root, ".devin", "rts",
                                           "map.json"))
        assert any(p["kind"] == "quest" for p in m["pois"])
        assert any(p["kind"] == "camp" for p in m["pois"])
        # editing a file lifts its tile patch live; 2nd lane -> contested
        pa = os.path.join(root, "alpha", "f.py")
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "edit",
            "payload": {"tool_input": {"file_path": pa, "lane": "A"},
                        "tool_response": "ok"}})
        st, snap = get(PORT, "/snapshot")
        m = snap["world"]["map"]
        assert sum(1 for f_ in m["fog"] if f_ == 2) >= 9, "no lit tiles"
        reg = {r["id"]: r for r in m["regions"]}
        assert reg["alpha"]["revealed"] is True
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "read",
            "payload": {"tool_input": {"file_path": pa, "lane": "B"},
                        "tool_response": "x=1"}})
        st, snap = get(PORT, "/snapshot")
        m = snap["world"]["map"]
        assert 2 in m["mark"], "contested tile not marked"
        # a stale touch stays explored (dim), not lit
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "read", "ts":
            time.time() - 400,
            "payload": {"tool_input": {"file_path": os.path.join(
                root, "beta", "g.py"), "lane": "A"},
                        "tool_response": ""}})
        st, snap = get(PORT, "/snapshot")
        m = snap["world"]["map"]
        assert 1 in m["fog"] and 2 in m["fog"], "fog dims/lits missing"
        print("PASS world map (territories, plots, fog, contested, pois)")

        # #123 buildings: pinned to real plots; detail endpoint = real data
        os.makedirs(os.path.join(root, ".devin", "agents"),
                    exist_ok=True)
        os.makedirs(os.path.join(root, ".devin", "memory"),
                    exist_ok=True)
        with open(os.path.join(root, ".devin", "agents",
                               "implementer.md"), "w") as f:
            f.write("# implementer\n")
        with open(os.path.join(root, ".devin", "memory", "m1.md"),
                  "w") as f:
            f.write("# note\n")
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "read_subagent",
            "payload": {"tool_input": {"agent_id": "lane1"},
                        "tool_response": "task failed with error"}})
        st, snap = get(PORT, "/snapshot")
        blds = {b["id"]: b for b in snap["world"]["buildings"]}
        regmap = {r["id"]: {tuple(p) for p in r["plots"]}
                  for r in snap["world"]["map"]["regions"]}
        for b in blds.values():
            p = b["pos"]
            assert p and (tuple(p["xy"]) in regmap[p["region"]]
                          or p["plot"] == -1), (b["id"], p)
        st, d = get(PORT, "/buildings/tavern")
        assert st == 200 and any(
            r["profile"] == "implementer" for r in d["roster"]), d
        st, d = get(PORT, "/buildings/library")
        assert any(e["file"] == "m1.md" for e in d["entries"]), d
        st, d = get(PORT, "/buildings/watchtower")
        lg = {l["id"]: l for l in d["ledgers"]}
        assert lg["eff"]["pass"] == 1 and lg["eff"]["fail"] == 1
        st, d = get(PORT, "/buildings/barracks")
        assert any(c["cls"] == "Knight" for c in d["classes"])
        assert any(i.get("profile") == "researcher" for i in d["queue"])
        st, d = get(PORT, "/buildings/altar")
        assert any(f["id"] == "lane1" for f in d["fallen"]), d
        st, d = get(PORT, "/buildings/portal")
        assert "remote" in d
        st, d = get(PORT, "/buildings/nope")
        assert st == 404
        print("PASS buildings (plots + real detail endpoints)")

        # #124 minimap/camera: upserts carry a map ping hint; order intents
        ws_drain(ws)
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "edit",
            "payload": {"tool_input": {"file_path": pa, "lane": "A"},
                        "tool_response": "ok2"}})
        h = ws_until_hint(ws, ("file", "contested"))
        assert len(h["xy"]) == 2, h
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "edit",
            "payload": {"tool_input": {"file_path": pa, "lane": "B"},
                        "tool_response": "ok3"}})
        h = ws_until_hint(ws, ("contested",))
        post(PORT, "/event", {
            "type": "decision.created",
            "payload": {"kind": "PermissionRequest"}})
        h = ws_until_hint(ws, ("decision",))
        assert post(PORT, "/intent", {"kind": "order", "to": "lane1",
                    "order": "move", "x": 3, "y": 4}) == 200
        print("PASS minimap pings (upsert hints) + order intent")

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
