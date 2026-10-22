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
    # #132 fixtures must exist before the daemon builds its map layout:
    # new top-level dirs become regions, so creating them mid-test would
    # diverge the replayed world from the live one
    for s in ("testing", "debugging", "gates", "zz-unsorted"):
        sd = os.path.join(root, "skills", s)
        os.makedirs(sd, exist_ok=True)
        with open(os.path.join(sd, "SKILL.md"), "w") as f:
            f.write("---\nname: %s\n---\n" % s)
    os.makedirs(os.path.join(root, "agents"), exist_ok=True)
    with open(os.path.join(root, "agents", "caster.md"), "w") as f:
        f.write("---\nname: caster\nmodel: swe-2-medium\n---\n"
                "Skills to invoke: `testing` `gates`\n")
    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    with open(os.path.join(root, "data", "bundle-models.json"), "w") as f:
        json.dump({"default_subagent_model": "swe-2-max",
                   "models": [
                       {"id": "swe-2-medium", "effort": "medium",
                        "context_window": 100},
                       {"id": "swe-2-max", "effort": "max",
                        "context_window": 100,
                        "is_default_subagent": True}]}, f)
    with open(os.path.join(root, "config.json"), "w") as f:
        json.dump({"agent": {"subagent_model": "swe-2-max"}}, f)
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    with open(os.path.join(root, "scripts", "memory-retrieval.py"),
              "w") as f:
        f.write("# cue-anchored retrieval of whole notes\n"
                "TOP_K = 3\ncues = []\n")
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
        # #136 day/night: session anchor is the first event ts
        assert isinstance(w["started"], (int, float)), w.get("started")
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
        # 3x3 patch interior; hashed file tile may sit on the map edge
        # (corner min = 4 lit), so the floor is the corner bound.
        assert sum(1 for f_ in m["fog"] if f_ == 2) >= 4, "no lit tiles"
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
        with open(os.path.join(root, "mcp_config.json"), "w") as f:
            json.dump({"mcpServers": {"gh": {"command": "gh-mcp"}}}, f)
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "mcp_call_tool",
            "payload": {"tool_input": {"server_name": "gh",
                                       "tool_name": "list_prs"}}})
        st, d = get(PORT, "/buildings/marketplace")
        assert st == 200 and any(
            s["name"] == "gh" and s["tools"] == 1
            for s in d["servers"]), d
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

        # #125 unit model: kit/tier on heroes, ambient workers with path
        st, snap = get(PORT, "/snapshot")
        w2 = snap["world"]
        lane1 = {u["id"]: u for u in w2["units"]}["lane1"]
        assert lane1["kit"] and lane1["tier"] in ("Footman", "Knight")
        assert any(wk.get("from") and wk.get("to")
                   for wk in w2["workers"]), w2["workers"]
        print("PASS unit model (kit/tier + worker scurry paths)")

        # #126 command card: targeted orders land as real intent files
        # with the quest ref the UI resolved from the quest POI marker
        assert post(PORT, "/intent", {
            "kind": "order", "to": "lane1", "order": "attack",
            "x": 5, "y": 6, "quest": "01-t"}) == 200
        assert post(PORT, "/intent", {
            "kind": "order", "to": "lane1", "order": "ability",
            "ability": "Farsight"}) == 200
        assert post(PORT, "/intent", {
            "kind": "order", "to": "lane1", "order": "hold"}) == 200
        idir = os.path.join(root, ".devin", "rts", "intents")
        ints = [json.load(open(os.path.join(idir, fn),
                             encoding="utf-8"))
                for fn in os.listdir(idir)]
        atk = [i for i in ints if i.get("order") == "attack"]
        assert atk and atk[-1]["to"] == "lane1" and \
            atk[-1]["quest"] == "01-t" and atk[-1]["x"] == 5, atk
        assert any(i.get("order") == "ability" and
                   i.get("ability") == "Farsight" for i in ints), ints
        assert any(i.get("order") == "hold" for i in ints), ints
        print("PASS command card orders -> intents/ (attack+quest, "
              "ability, hold)")

        # #127 orders queue: shift-queued waypoints carry lifecycle state
        # from the intent file (pending -> queued; surfaced -> ack)
        for n, xy in enumerate(((8, 8), (12, 8), (12, 14))):
            assert post(PORT, "/intent", {
                "kind": "order", "to": "lane1", "order": "move",
                "id": "wp%d" % n,
                "x": xy[0], "y": xy[1], "queue": True}) == 200
        st, snap = get(PORT, "/snapshot")
        lane1 = {u["id"]: u for u in snap["world"]["units"]}["lane1"]
        moves = [o for o in lane1["orders"] if o.get("queue")]
        assert len(moves) == 3 and all(o["state"] == "queued"
                                     for o in moves), moves
        assert [ (o["x"], o["y"]) for o in moves] == \
            [(8, 8), (12, 8), (12, 14)], moves     # queue order preserved
        # ghost clears: once rts-intents.py surfaces the file, the order
        # is acknowledged instead of queued
        idir = os.path.join(root, ".devin", "rts", "intents")
        first = os.path.join(idir, moves[0]["id"] + ".json")
        it = json.load(open(first, encoding="utf-8"))
        it["status"] = "surfaced"
        with open(first, "w", encoding="utf-8") as f:
            json.dump(it, f)
        st, snap = get(PORT, "/snapshot")
        lane1 = {u["id"]: u for u in snap["world"]["units"]}["lane1"]
        mv = [o for o in lane1["orders"] if o.get("queue")]
        assert mv[0]["state"] == "acknowledged" and \
            mv[1]["state"] == "queued", mv
        # rally point: set_rally on barracks applies to the next spawn
        m = snap["world"]["map"]
        aidx = [r["id"] for r in m["regions"]].index("alpha")
        t = next(i for i, v in enumerate(m["tile_region"]) if v == aidx)
        assert post(PORT, "/intent", {
            "kind": "order", "to": "barracks", "order": "set_rally",
            "id": "rally1", "x": t % m["w"], "y": t // m["w"]}) == 200
        st, d = get(PORT, "/buildings/barracks")
        assert d["rally"] and d["rally"]["region"] == "alpha", d["rally"]
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "run_subagent",
            "payload": {"tool_input": {"profile": "implementer",
                                       "task": "rallied job",
                                       "is_background": True},
                        "tool_response": {"agent_id": "rallied1"}}})
        st, snap = get(PORT, "/snapshot")
        ru = {u["id"]: u for u in snap["world"]["units"]}["rallied1"]
        assert ru["lane"] == "alpha", ru
        bb = {b["id"]: b for b in snap["world"]["buildings"]}["barracks"]
        assert bb["rally"]["region"] == "alpha", bb
        # idle worker list: hero idle (no events >120s) with no orders
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "run_subagent",
            "ts": time.time() - 200,
            "payload": {"tool_input": {"profile": "debugger",
                                       "task": "afk", "is_background": True},
                        "tool_response": {"agent_id": "idlehero"}}})
        st, snap = get(PORT, "/snapshot")
        iu = {u["id"]: u for u in snap["world"]["units"]}["idlehero"]
        assert iu["status_live"] == "idle", iu
        assert "idlehero" in snap["world"]["idle"], snap["world"]["idle"]
        assert "lane1" not in snap["world"]["idle"]  # has queued orders
        print("PASS orders queue (waypoints, ack state, rally, idle)")

        # #130 quests: DAG blocking, main/side split, assign -> hero tracks
        # the issue's ledger gates, evidence loot, quest feed lines
        issdir = os.path.join(root, ".devin", "scratch", "eff", "issues")
        with open(os.path.join(issdir, "02-t.md"), "w",
                  encoding="utf-8") as f:
            f.write("# t2\n\nStatus: ready-for-agent\nBlocked by: 01-t\n")
        with open(os.path.join(ldir, "02-t.md"), "w", encoding="utf-8") as f:
            f.write("# G\n\n- [x] A1: ok\n  EVIDENCE: loot-a1\n"
                    "- [x] A2: ok\n  EVIDENCE: loot-a2\n")
        assert post(PORT, "/intent",
                    {"kind": "goal", "text": "ship v3.8.0"}) == 200
        st, snap = get(PORT, "/snapshot")
        qs = {q["id"]: q for q in snap["world"]["quests"]}
        assert qs["main-quest"]["kind"] == "main" and \
            qs["main-quest"]["title"] == "ship v3.8.0", qs["main-quest"]
        assert qs["01-t"]["kind"] == "side" and not qs["01-t"]["blocked"]
        assert qs["02-t"]["blocked"] is True and \
            qs["02-t"]["deps"] == ["01-t"], qs["02-t"]  # DAG resolution
        assert qs["02-t"]["gates"] == {"pass": 2, "fail": 0, "total": 2}
        assert qs["01-t"]["ledger"] == "eff"  # effort-ledger fallback
        pois = {p["ref"]: p for p in snap["world"]["map"]["pois"]
                if p["kind"] == "quest"}
        assert pois["02-t"]["qst"] == "blocked", pois["02-t"]
        assert pois["01-t"]["qst"] == "failed"  # effort ledger has a fail
        # assign: attack order carrying the issue ref binds hero -> quest;
        # HP/loot then track the issue's own ledger (2/2 pass, evidence)
        assert post(PORT, "/intent", {
            "kind": "order", "to": "lane1", "order": "attack",
            "x": 5, "y": 6, "quest": "02-t"}) == 200
        st, snap = get(PORT, "/snapshot")
        w3 = snap["world"]
        lane1 = {u["id"]: u for u in w3["units"]}["lane1"]
        assert lane1["quest"] == "02-t", lane1
        assert lane1["hp"] == 100 and not lane1.get("gate_fail"), lane1
        assert lane1["inventory"][0]["quest"] == "02-t" and \
            lane1["inventory"][0]["evidence"] == "loot-a1", lane1
        qs = {q["id"]: q for q in w3["quests"]}
        assert qs["02-t"]["assignees"] == ["lane1"], qs["02-t"]
        feed_txt = [l["text"] for l in w3["feed"] if l["kind"] == "quest"]
        assert any("Quest accepted: 02-t" in t for t in feed_txt), feed_txt
        assert any("Objective complete (2/2)" in t for t in feed_txt)
        assert any("Quest failed: 01-t" in t for t in feed_txt), feed_txt
        # completing the issue flips the marker to the rewards stamp
        with open(os.path.join(issdir, "01-t.md"), "w",
                  encoding="utf-8") as f:
            f.write("# t\n\nStatus: resolved\nBlocked by: -\n")
        st, snap = get(PORT, "/snapshot")
        qs = {q["id"]: q for q in snap["world"]["quests"]}
        assert qs["02-t"]["blocked"] is False  # dep resolved
        pois = {p["ref"]: p for p in snap["world"]["map"]["pois"]
                if p["kind"] == "quest"}
        assert pois["01-t"]["qst"] == "done", pois["01-t"]
        print("PASS quest log (DAG block, assign->intent, ledger HP, "
              "loot, feed, marker states)")

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

        # #128 comms feed: real events -> flavored radio chatter lines.
        # Events already sent above cover spawn / debrief(done+failed) /
        # file position / council decision / orders; add a steering
        # message intent and out-of-band surfaces (mailbox, heartbeat).
        assert post(PORT, "/intent", {
            "kind": "message", "to": "abc12345",
            "text": "re-check the ledger"}) == 200
        # mailbox deposit (rts-intents.py format) + heartbeat note land
        # via the daemon's comms poller on the next tick
        mbx = os.path.join(root, ".devin", "mailboxes", "abc12345",
                           "inbox")
        os.makedirs(mbx, exist_ok=True)
        with open(os.path.join(mbx, "msg-t1.json"), "w") as f:
            json.dump({"id": "msg-t1", "from": "rts-ui",
                       "to": "abc12345", "type": "task",
                       "content": "status?", "status": "unread"}, f)
        agd = os.path.join(root, ".devin", "rts", "agents", "abc12345")
        os.makedirs(agd, exist_ok=True)
        with open(os.path.join(agd, "status.json"), "w") as f:
            json.dump({"note": "tests 46/46 green"}, f)
        feed = []
        for _ in range(30):
            st, snap = get(PORT, "/snapshot")
            feed = snap["world"].get("feed") or []
            if any(l["kind"] == "raven" for l in feed) and \
                    any(l["kind"] == "note" for l in feed):
                break
            time.sleep(0.3)
        by_kind = {}
        for l in feed:
            by_kind.setdefault(l["kind"], []).append(l)
        # 5+ distinct flavors, all with real payload data
        for k in ("spawn", "debrief", "position", "council", "order",
                  "steering", "raven", "note"):
            assert k in by_kind, (k, feed)
        sp = [l for l in by_kind["spawn"]
              if "takes the field" in l["text"]][0]
        assert sp["who"].startswith("Far Seer"), sp      # researcher cls
        assert "probe task" in sp["text"], sp
        assert any(l["who"] == "Cmdr" and "requisition" in l["text"]
                   for l in by_kind["spawn"])            # spawn intent
        deb = [l for l in by_kind["debrief"] if "46" not in l["text"]]
        assert any("failed" in l["text"] or "retreat" in l["text"]
                   or "unit down" in l["text"] for l in deb), deb
        pos = by_kind["position"][0]
        assert "alpha/f.py" in pos["text"], pos          # real file path
        assert any("rallied job" in l["text"] for l in by_kind["spawn"])
        st_line = by_kind["steering"][0]
        assert st_line["uid"] == "abc12345", st_line     # right agent id
        assert "Far Seer-1" in st_line["text"], st_line  # name resolved
        assert "re-check the ledger" in st_line["text"], st_line
        rv = by_kind["raven"][0]
        assert "rts-ui" in rv["text"] and "Far Seer-1" in rv["text"], rv
        assert rv["uid"] == "abc12345", rv
        nt = by_kind["note"][0]
        assert "tests 46/46 green" in nt["text"], nt
        mails = snap["world"].get("mail") or []
        assert any(m["id"] == "msg-t1" for m in mails), mails
        # the deposit became a real event in events.jsonl
        evs = [json.loads(l) for l in open(log, encoding="utf-8")
               if l.strip()]
        assert any(e["type"] == "mail.deposit" for e in evs)
        assert any(e["type"] == "agent.note" for e in evs)
        # scrollback is event-sourced: feed rebuilds identically (the
        # replay equality check below covers world.feed byte-for-byte)
        print("PASS comms feed (%d lines, %d kinds, raven+note poller)"
              % (len(feed), len(by_kind)))

        # #129 war council: a PermissionRequest hook event becomes a real
        # pending decision (same file shape rts-decision.py --create
        # writes) + a decision.created event/feed/ping; pending decisions
        # stack; answers go through the .response path --wait consumes.
        rts_dec = os.path.abspath(os.path.join(
            HERE, "..", "..", "scripts", "rts-decision.py"))
        ws_drain(ws)
        assert post(PORT, "/event", {
            "type": "hook.permissionrequest",
            "hook": "PermissionRequest", "tool": "exec",
            "session_id": "eff",
            "payload": {"tool_name": "exec",
                        "tool_input": {"command": "rm -rf /tmp/x"},
                        "session_id": "eff"}}) == 200
        assert post(PORT, "/event", {
            "type": "hook.permissionrequest",
            "hook": "PermissionRequest", "tool": "write",
            "session_id": "eff",
            "payload": {"tool_name": "write",
                        "tool_input": {"file_path": "/etc/passwd"},
                        "session_id": "eff", "timeout": 30}}) == 200
        h = ws_until_hint(ws, ("decision",))
        st, snap = get(PORT, "/snapshot")
        perm = [d for d in snap["decisions"]
                if d.get("kind") == "permission"]
        assert len(perm) == 2, snap["decisions"]
        perm.sort(key=lambda d: d["created_at"])
        p1, p2 = perm
        assert "exec" in p1["prompt"] and "rm -rf" in p1["prompt"], p1
        assert p1["options"] == ["allow", "deny"]
        assert p1["status"] == "pending" and p1["requester"] == "eff"
        dfile = os.path.join(root, ".devin", "rts", "decisions",
                             p1["id"] + ".json")
        assert os.path.isfile(dfile)
        # OOB choice -> 400; real answer -> .response file; replay -> 409
        assert post(PORT, "/decisions/%s/answer" % p1["id"],
                    {"choice": 9}) == 400
        assert post(PORT, "/decisions/%s/answer" % p1["id"],
                    {"choice": 0}) == 200
        assert post(PORT, "/decisions/%s/answer" % p1["id"],
                    {"choice": 0}) == 409
        resp = json.load(open(dfile + ".response", encoding="utf-8"))
        assert resp["choice"] == 0, resp
        # stacked queue intact: the second decision is still pending
        st, snap = get(PORT, "/snapshot")
        rest = [d["id"] for d in snap["decisions"]
                if d["status"] == "pending"]
        assert p2["id"] in rest and p1["id"] not in rest, rest
        # the real CLI consumer resolves via the .response file
        out = subprocess.check_output(
            [sys.executable, rts_dec, "--wait", p1["id"]],
            cwd=root, timeout=10).decode()
        ans = json.loads(out)
        assert ans["status"] == "answered" and ans["choice"] == 0, ans
        # fail-closed: an unanswered decision times out to last option
        d2p = os.path.join(root, ".devin", "rts", "decisions",
                           p2["id"] + ".json")
        d2 = json.load(open(d2p, encoding="utf-8"))
        d2["timeout"] = 0.3
        with open(d2p, "w", encoding="utf-8") as f:
            json.dump(d2, f)
        out = subprocess.check_output(
            [sys.executable, rts_dec, "--wait", p2["id"]],
            cwd=root, timeout=10).decode()
        ans = json.loads(out)
        assert ans["status"] == "timeout" and \
            ans["choice"] == len(d2["options"]) - 1, ans
        # out-of-band create (the real rts-decision.py --create path) is
        # picked up by the daemon's decision poller -> decision.created
        oob = subprocess.check_output(
            [sys.executable, rts_dec, "--create"], cwd=root,
            input=b'{"kind":"question","prompt":"merge now?",'
                  b'"timeout":60}', timeout=10).decode().strip()
        for _ in range(30):
            st, snap = get(PORT, "/snapshot")
            ids = [d["id"] for d in snap["decisions"]]
            feed = snap["world"].get("feed") or []
            if oob in ids and any("question awaits ruling" in
                                  l["text"] for l in feed):
                break
            time.sleep(0.3)
        else:
            raise AssertionError("oob decision never surfaced: %s" % ids)
        print("PASS war council (permissionrequest->decision, stack, "
              "answer/.response, fail-closed timeout, oob create)")

        # #131 economy: PostToolUse hook output -> income rate, last-5
        # trend, per-lane burn on the hero, supply split by kind,
        # thresholds straight from data/context-budget.json defaults
        out_txt = "x" * 400   # 100 est tokens + 200 call overhead = 300
        assert post(PORT, "/event", {
            "type": "hook.posttooluse", "hook": "PostToolUse",
            "tool": "exec",
            "payload": {"tool_input": {"command": "tail log",
                                       "lane": "eff"},
                        "tool_response": out_txt}}) == 200
        st, snap = get(PORT, "/snapshot")
        r = snap["world"]["resources"]
        assert r["income_min"] >= 300, r                    # last 60s sum
        assert r["income_last5"][-1] == 300, r["income_last5"]
        assert len(r["income_last5"]) <= 5
        assert r["thresholds"] == {"warn": 60, "crit": 75,
                                  "clear": 80}, r["thresholds"]
        assert r["supply_heroes"] == r["supply_used"]
        assert r["supply_minions"] == 0, r                  # zz9 killed
        assert r["window"] > 0
        lane1 = {u["id"]: u for u in snap["world"]["units"]}["lane1"]
        assert lane1["burn"] >= 300, lane1            # lane "eff" spend
        assert "turns_left" in lane1                  # None w/o heartbeat
        # a hero whose lane saw no burn reports 0, not a guess
        idlehero = {u["id"]: u for u in
                    snap["world"]["units"]}["idlehero"]
        assert idlehero["burn"] == 0 and idlehero["turns_left"] is None
        print("PASS economy HUD (income rate, last5, thresholds, "
              "supply split, per-hero burn)")

        # #132 tech tree: real skills/ dirs grouped by GDD school, cast
        # state from `skill` tool events, hero spellbook from the profile
        # sheet, model tier from bundle-models.json effort, armory pin
        # from config.json, doctrines from real memory scripts/files
        # (fixtures created before daemon start - see top of main)
        with open(os.path.join(root, ".devin", "memory", "MOC.md"),
                  "w") as f:
            f.write("# index\n")
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "skill",
            "payload": {"tool_input": {"command": "invoke",
                                       "skill": "testing", "lane": "eff"},
                        "tool_response": "ok"}})
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "skill",
            "payload": {"tool_input": {"command": "invoke",
                                       "skill": "testing", "lane": "eff"},
                        "tool_response": "ok2"}})
        post(PORT, "/event", {
            "type": "hook.posttooluse", "tool": "run_subagent",
            "payload": {"tool_input": {"profile": "caster",
                                       "task": "spell duty",
                                       "is_background": True,
                                       "lane": "eff"},
                        "tool_response": {"agent_id": "caster1"}}})
        st, snap = get(PORT, "/snapshot")
        tech = snap["world"]["tech"]
        by_school = {s["id"]: s for s in tech["schools"]}
        craft = {sp["name"]: sp for sp in by_school["Craft"]["spells"]}
        assert craft["testing"]["casts"] == 2, craft["testing"]
        assert craft["testing"]["path"].endswith(
            os.path.join("skills", "testing", "SKILL.md"))
        assert craft["debugging"]["casts"] == 0     # known, never cast
        assert any(sp["name"] == "zz-unsorted"
                   for sp in by_school["Unsorted"]["spells"])
        assert sum(len(s["spells"]) for s in tech["schools"]) == 4
        assert tech["armory"]["subagent_model"] == "swe-2-max"
        assert "config.json" in tech["armory"]["pin"]
        assert any(t["id"] == "swe-2-medium"
                   for t in tech["armory"]["tiers"])
        docs = {d["id"]: d for d in tech["doctrines"]}
        assert len(docs) == 8
        assert docs["document"]["in_use"] is True and \
            docs["document"]["evidence"], docs["document"]
        assert docs["hierarchical"]["in_use"] is True   # MOC.md exists
        assert docs["semantic"]["in_use"] is False and \
            docs["semantic"]["evidence"] == []
        cu = {u["id"]: u for u in snap["world"]["units"]}["caster1"]
        assert cu["model"] == "swe-2-medium"          # profile pin wins
        assert cu["tier"] == "Footman"                # effort medium
        book = {s["name"]: s for s in cu["spellbook"]}
        assert set(book) == {"testing", "gates"}, book
        assert book["testing"]["casts"] == 2 and book["gates"]["casts"] == 0
        assert any(l["kind"] == "spell" and "casts testing" in l["text"]
                   for l in snap["world"]["feed"])
        st, d = get(PORT, "/buildings/library")
        assert st == 200 and d["spellbook"] and d["doctrines"] \
            and d["armory"]["subagent_model"] == "swe-2-max", d.keys()
        assert post(PORT, "/intent", {
            "kind": "order", "to": "caster1", "order": "cast",
            "skill": "testing"}) == 200
        idir = os.path.join(root, ".devin", "rts", "intents")
        ints = [json.load(open(os.path.join(idir, fn), encoding="utf-8"))
                for fn in os.listdir(idir)]
        assert any(i.get("order") == "cast" and
                   i.get("skill") == "testing" for i in ints), ints
        # the cast intent created a new event/order - refresh so the
        # replay equality check below compares the same event horizon
        st, snap = get(PORT, "/snapshot")
        print("PASS tech tree (schools, cast state, hero spellbook, "
              "armory tiers, doctrines, cast intent)")

        # #133 alerts: a failed ledger gate surfaces as a persistent
        # breach on its territory (region resolved via the linked issue
        # file's tile); sealing every gate clears the alarm state, so
        # polling remote/PWA clients track it without push infra
        st, snap = get(PORT, "/snapshot")
        br = {b["ledger"]: b for b in snap["world"]["breaches"]}
        assert "eff" in br, snap["world"]["breaches"]
        assert br["eff"]["region"] == ".devin" and \
            "G2" in br["eff"]["gates"], br["eff"]
        assert len(br["eff"]["xy"]) == 2
        with open(os.path.join(ldir, "eff.md"), "w", encoding="utf-8") as f:
            f.write("# G\n\n- [x] G1: ok\n  EVIDENCE: ev\n"
                    "- [x] G2: fixed\n  EVIDENCE: repaired\n"
                    "- [x] G3: done\n  EVIDENCE: ok\n")
        st, snap = get(PORT, "/snapshot")
        assert all(b["ledger"] != "eff"
                   for b in snap["world"]["breaches"])
        print("PASS breach alarms (persistent territory, seal clears)")

        # #135 replay + spectator + match history + score screen.
        # Freeze the log at this point into a copy so the live daemon's
        # poller appends do not shift the replay horizon mid-check.
        sys.path.insert(0, HERE)
        import world as worldmod_pre
        evs_now = [json.loads(l) for l in
                   open(log, encoding="utf-8") if l.strip()]
        copylog = os.path.join(root, ".devin", "rts", "sessions")
        os.makedirs(copylog, exist_ok=True)
        copylog = os.path.join(copylog, "match-1.jsonl")
        with open(copylog, "w", encoding="utf-8") as f:
            for e in evs_now:
                f.write(json.dumps(e) + "\n")

        # score screen: real aggregates over the same snapshot path
        st, sc = get(PORT, "/score")
        assert st == 200 and sc["gates_total"] > 0, sc
        assert sc["quests_total"] >= 2 and sc["quests_done"] >= 1, sc
        assert any(h["id"] == "lane1" for h in sc["heroes"]), sc
        assert sc["heroes"] == sorted(
            sc["heroes"], key=lambda u: (-u["xp"], u["id"]))
        assert sc["gold"] > 0 and sc["calls"] > 0 and \
            sc["duration_s"] >= 0, sc
        assert sc["goal"] == "ship v3.8.0", sc

        # match history: both logs listed with real per-session stats
        st, ss = get(PORT, "/sessions")
        assert st == 200 and len(ss) >= 2, ss
        ids = [s["id"] for s in ss]
        assert "events.jsonl" in ids, ids
        m1 = [s for s in ss if s["id"].endswith("match-1.jsonl")][0]
        assert m1["events"] == len(evs_now) and m1["agents"] >= 4, m1
        assert m1["tokens"] == sc["gold"] or m1["tokens"] > 0, m1
        assert m1["score"]["heroes"], m1
        print("PASS score screen + match history (%d sessions)" % len(ss))

        # spectator: --remote mints a read-only token; presenting it
        # (even loopback) scopes every POST to 403 - server-enforced
        RPORT = PORT + 4
        # separate root: the remote daemon writes its own events.jsonl
        # (auth/intent events), which must not shift the main log's
        # replay horizon for the #120 determinism check below
        rroot = tempfile.mkdtemp()
        rproc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "rtsd.py"),
             "--port", str(RPORT), "--root", rroot, "--remote", "2"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            rj = os.path.join(rroot, ".devin", "rts", "remote.json")
            for _ in range(50):
                if os.path.isfile(rj):
                    break
                time.sleep(0.1)
            else:
                raise AssertionError("remote.json never written")
            toks = json.load(open(rj, encoding="utf-8"))
            assert toks["token"] and toks["spectator_token"] and \
                toks["token"] != toks["spectator_token"]

            def post_tok(port, path, obj, tok):
                c = http.client.HTTPConnection("127.0.0.1", port,
                                               timeout=5)
                c.request("POST", path, json.dumps(obj),
                          {"Content-Type": "application/json",
                           "X-RTS-Token": tok})
                r = c.getresponse(); r.read()
                return r.status

            def get_tok(port, path, tok):
                c = http.client.HTTPConnection("127.0.0.1", port,
                                               timeout=5)
                c.request("GET", path,
                          headers={"X-RTS-Token": tok})
                r = c.getresponse()
                return r.status, json.loads(r.read())

            st, snap = get_tok(RPORT, "/snapshot",
                               toks["spectator_token"])
            assert st == 200 and snap["client_role"] == "spectator", \
                snap.get("client_role")
            assert post_tok(RPORT, "/intent",
                            {"kind": "goal", "text": "x"},
                            toks["spectator_token"]) == 403
            assert post_tok(RPORT, "/decisions/d1/answer",
                            {"choice": 0},
                            toks["spectator_token"]) == 403
            assert post_tok(RPORT, "/event", {"type": "x"},
                            toks["spectator_token"]) == 403
            assert post_tok(RPORT, "/intent",
                            {"kind": "goal", "text": "admin ok"},
                            toks["token"]) == 200
            st, snap = get_tok(RPORT, "/snapshot", toks["token"])
            assert snap["client_role"] == "admin"
            print("PASS spectator (read-only token, POSTs 403 "
                  "server-side, admin unaffected)")
        finally:
            rproc.terminate()
            try:
                rproc.wait(3)
            except subprocess.TimeoutExpired:
                rproc.kill()

        # replay mode: --replay <log> serves a deterministic rebuild;
        # mutating POSTs are denied, /replay drives play/pause/seek/speed
        PPORT = PORT + 6
        pproc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "rtsd.py"),
             "--port", str(PPORT), "--root", root,
             "--replay", copylog],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(50):
                try:
                    st, body = get(PPORT, "/health")
                    if st == 200:
                        break
                except Exception:
                    time.sleep(0.1)
            else:
                raise AssertionError("replay daemon did not start")
            st, rp = get(PPORT, "/replay")
            assert rp["total"] == len(evs_now) and rp["index"] == 0 \
                and not rp["playing"] and not rp["done"], rp
            st, snap = get(PPORT, "/snapshot")
            assert snap["mode"] == "replay" and snap["replay"], snap
            assert post(PPORT, "/intent",
                        {"kind": "goal", "text": "x"}) == 403
            assert post(PPORT, "/event", {"type": "x"}) == 403
            # jump-to-event: scrub to the end = deterministic rebuild
            assert post(PPORT, "/replay",
                        {"action": "seek",
                         "index": rp["total"]}) == 200
            st, rp = get(PPORT, "/replay")
            assert rp["done"] and rp["index"] == rp["total"], rp
            st, snap = get(PPORT, "/snapshot")
            got_ids = {u["id"] for u in snap["world"]["units"]}
            live_ids = {u["id"] for u in
                        worldmod_pre.World.replay(
                            root, evs_now).snapshot()["units"]}
            assert got_ids == live_ids, (got_ids ^ live_ids)
            got_feed = [l["text"] for l in snap["world"]["feed"]]
            live_feed = [l["text"] for l in
                         worldmod_pre.World.replay(
                             root, evs_now).snapshot()["feed"]]
            assert got_feed == live_feed
            # scrub back to 0 then play at 4x: visuals stream as the
            # same upserts live events produce, ending on the score
            assert post(PPORT, "/replay",
                        {"action": "seek", "index": 0}) == 200
            st, snap = get(PPORT, "/snapshot")
            assert len(snap["world"]["units"]) == 0
            assert post(PPORT, "/replay",
                        {"action": "play", "speed": 4}) == 200
            for _ in range(200):
                st, rp = get(PPORT, "/replay")
                if rp["done"]:
                    break
                assert rp["speed"] == 4
                time.sleep(0.2)
            assert rp["done"], rp          # full tape at 4x
            st, sc2 = get(PPORT, "/score")
            assert {h["id"] for h in sc2["heroes"]} == \
                {h["id"] for h in sc["heroes"]}, sc2
            assert sc2["gold"] == sc["gold"], (sc2["gold"], sc["gold"])
            print("PASS replay mode (seek/play@4x/403s, deterministic "
                  "world + feed, score parity)")
        finally:
            pproc.terminate()
            try:
                pproc.wait(3)
            except subprocess.TimeoutExpired:
                pproc.kill()

        # #157 live weather + mode override
        st, wx = get(PORT, "/weather")
        assert st == 200 and wx.get("ok") is True and "wind_kph" in wx, wx
        assert "temp_c" in wx and "condition" in wx and "wind_deg" in wx, wx
        assert post(PORT, "/weather", {"mode": "storm"}) == 200
        st, wx2 = get(PORT, "/weather")
        assert wx2.get("mode") == "storm" and wx2.get("condition") == "storm"
        assert post(PORT, "/weather", {"mode": "live"}) == 200
        print("PASS weather endpoint (live forecast + mode override)")

        # #172 Explorer (/files) + Git Codex (/git, /git/diff)
        st, fls = get(PORT, "/files")
        assert st == 200 and fls.get("ok") is True, fls
        assert any(f["path"].endswith("f.py") and f["badge"] == "PY"
                   for f in fls["files"]), fls
        st, gcx = get(PORT, "/git")
        assert st == 200 and gcx.get("ok") is True and "changes" in gcx, gcx
        st, gdf = get(PORT, "/git/diff?path=alpha/f.py")
        assert st == 200 and gdf.get("ok") is True and "diff" in gdf, gdf
        st_bad, _ = get(PORT, "/git/diff?path=../../etc/passwd")
        assert st_bad == 400
        print("PASS explorer (/files) + git codex (/git, /git/diff, traversal guard)")

        # #178 Scheduled Loops (/loops) + Integrated Terminal (/terminal)
        assert post(PORT, "/loops",
                    {"action": "create", "interval_m": 5,
                     "prompt": "Check gates"}) == 200
        st, lps = get(PORT, "/loops")
        assert st == 200 and len(lps.get("loops") or []) == 1, lps
        lid = lps["loops"][0]["id"]
        assert post(PORT, "/loops", {"action": "trigger", "id": lid}) == 200
        st, lps2 = get(PORT, "/loops")
        assert lps2["loops"][0]["iterations"] == 1, lps2
        assert post(PORT, "/loops", {"action": "stop", "id": lid}) == 200
        assert post(PORT, "/terminal", {"cmd": "echo rtsd-term-ok"}) == 200
        print("PASS campaigns/loops (/loops) + integrated terminal (/terminal)")

        # #120 determinism: replaying events.jsonl rebuilds the same world
        st, snap = get(PORT, "/snapshot")
        # #176 Collectible Skill Scrolls + Tiered Achievements in snapshot
        w_snap = snap["world"]
        assert len(w_snap.get("scrolls") or []) >= 1, w_snap.get("scrolls")
        assert len(w_snap.get("achievements") or []) >= 10, w_snap.get("achievements")
        assert any(a["id"] == "first_hero" and a["unlocked"]
                   for a in w_snap["achievements"]), w_snap["achievements"]
        # #190 Age of Mythology: Retold 5 Ages + Divine Favor + God Powers
        assert "age" in w_snap and w_snap["age"]["num"] >= 2, w_snap.get("age")
        assert w_snap["resources"].get("favor", 0) >= 25, w_snap["resources"]
        assert len(w_snap["age"].get("powers") or []) == 4, w_snap["age"]
        # #192 True Office Tycoon Mode: staff roster, departments, sprint, upgrades
        off = w_snap.get("office") or {}
        assert off.get("mode") == "office", off
        assert len(off.get("staff") or []) >= 1, off.get("staff")
        assert "sprint" in off and "progress" in off["sprint"], off.get("sprint")
        assert len(off.get("upgrades") or []) >= 5, off.get("upgrades")
        print("PASS skill scrolls + achievements + AoM 5 Ages & God Powers + Office Tycoon")
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
