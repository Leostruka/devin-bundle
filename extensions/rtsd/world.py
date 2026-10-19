"""world - event-sourced RTS world model for rtsd (GDD:
.devin/scratch/agentcraft-rts-v2/gdd.md).

Purity contract: World.apply(ev) mutates only event-derived state. All
time-derived fields (decay, idle, minion TTL, worker window) are computed
in snapshot(now) from stored timestamps, so replaying events.jsonl with
the same `now` reproduces an identical world dict. Stdlib only.
"""
import os
import re
import json
import time

CHARS_PER_TOKEN = 4
SUPPLY_CAP = 8          # concurrent-hero design cap (GDD supply/food)
WORKER_WINDOW_S = 60.0  # a hook firing keeps a peasant alive this long
MINION_TTL_S = 300.0    # a summoned shell unit fades without fresh signals
IDLE_AFTER_S = 120.0    # hero with no events this long reads as idle
STALE_AFTER_S = 600.0   # beyond this the hero is stale (signal lost)

HERO_CLASSES = {
    "implementer": "Knight", "debugger": "Ranger", "qa-ci": "Cleric",
    "reviewer": "Spellbreaker", "researcher": "Far Seer",
    "architect": "Archmage", "tech-lead": "Runesmith",
    "product-manager": "Herald", "scrum-master": "Marshal",
    "art-director": "Enchanter", "copywriter": "Bard",
    "security-auditor": "Inquisitor", "red-team-lead": "Shadowblade",
    "subagent_explore": "Scout", "subagent_general": "Squire",
    "domain": "Cartographer", "issue-tracker": "Chronicler",
    "repo-reviewer": "Inspector", "triage-labels": "Steward",
}

BUILDINGS = [
    ("town-hall", "Town Hall"),
    ("barracks", "Barracks"),
    ("tavern", "Tavern"),
    ("library", "Library"),
    ("watchtower", "Watchtower"),
    ("runeforge", "Runeforge"),
    ("vault", "Vault"),
    ("portal", "Portal"),
    ("marketplace", "Marketplace"),
    ("altar", "Altar"),
    ("trophy-hall", "Trophy Hall"),
]

# Which building a tool's activity lights up. File-touching tools own the
# terrain instead (they lift fog on their region, not a building).
TOOL_TO_BUILDING = {
    "run_subagent": "barracks", "read_subagent": "barracks",
    "skill": "library", "todo_write": "town-hall",
    "ask_user_question": "town-hall",
    "mcp_call_tool": "marketplace", "mcp_list_tools": "marketplace",
    "mcp_list_servers": "marketplace", "mcp_read_resource": "marketplace",
    "browser_preview": "watchtower", "exec": "town-hall",
    "get_output": "town-hall", "write_to_process": "town-hall",
    "kill_shell": "town-hall",
}

FILE_TOOLS = {"read", "write", "edit", "notebook_edit",
              "grep", "glob", "find_file_by_name", "apply_patch"}

_find_agent_id = None  # injected by rtsd (avoids duplicating the regex)
_read_json = None


def _agent_id(resp):
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


def _output_text(payload):
    out = payload.get("tool_output", payload.get("tool_response",
                                                 payload.get("result")))
    if out is None:
        return ""
    return out if isinstance(out, str) else json.dumps(out)


def _input_path(ti):
    for k in ("file_path", "notebook_path", "path"):
        v = ti.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def region_of(root, path):
    """Map a file path to its territory id = first path segment under root."""
    if not path:
        return None
    p = path.replace("\\", "/")
    r = root.replace("\\", "/").rstrip("/") + "/"
    if p.startswith(r):
        p = p[len(r):]
    elif not os.path.isabs(path):
        p = p.lstrip("./")
    else:
        return None
    seg = p.split("/")[0]
    return seg or None


def scan_issues(root):
    tasks = []
    scratch = os.path.join(root, ".devin", "scratch")
    if not os.path.isdir(scratch):
        return tasks
    for effort in sorted(os.listdir(scratch)):
        idir = os.path.join(scratch, effort, "issues")
        if not os.path.isdir(idir):
            continue
        for fn in sorted(os.listdir(idir)):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(idir, fn)
            try:
                head = open(p, encoding="utf-8").read(1500)
            except OSError:
                continue
            status = re.search(r"^Status:\s*(\S+)", head, re.M)
            blocked = re.search(r"^Blocked by:\s*(.+)", head, re.M)
            title = head.splitlines()[0].lstrip("# ").strip() if head else fn
            tasks.append({
                "id": fn[:-3], "effort": effort, "title": title,
                "status": status.group(1) if status else "needs-triage",
                "blocked_by": (blocked.group(1).strip() if blocked else ""),
            })
    return tasks


def scan_ledgers(root):
    """Parse .devin/ledgers/*.md: [x]=pass, [ ]=pending, [!]/[F]=fail."""
    ldir = os.path.join(root, ".devin", "ledgers")
    out = []
    if not os.path.isdir(ldir):
        return out
    for fn in sorted(os.listdir(ldir)):
        if not fn.endswith(".md"):
            continue
        try:
            lines = open(os.path.join(ldir, fn),
                         encoding="utf-8").read().splitlines()
        except OSError:
            continue
        gates, cur = [], None
        for ln in lines:
            m = re.match(r"- \[([xX !fF])\]\s*(\S+?):?\s+(.*)", ln)
            if m:
                mark = m.group(1).lower()
                cur = {"id": m.group(2), "title": m.group(3).strip(),
                       "state": {"x": "pass", " ": "pending"}.get(mark, "fail")}
                gates.append(cur)
                continue
            if cur:
                mm = re.match(r"\s+(CHECK|EXPECT|EVIDENCE):\s*(.*)", ln)
                if mm:
                    cur[mm.group(1).lower()] = mm.group(2).strip()
        out.append({"id": fn[:-3],
                    "path": os.path.join(".devin", "ledgers", fn),
                    "gates": gates})
    return out


def load_thresholds(root):
    try:
        with open(os.path.join(root, "data", "context-budget.json"),
                  encoding="utf-8") as f:
            t = json.load(f).get("thresholds", {})
            return (t.get("warn_pct", 60), t.get("critical_pct", 75),
                    t.get("clear_recommended_pct", 80))
    except Exception:
        return (60, 75, 80)


def default_window(root):
    try:
        with open(os.path.join(root, "data", "bundle-models.json"),
                  encoding="utf-8") as f:
            for m in json.load(f).get("models", []):
                if m.get("is_default_parent"):
                    return m.get("context_window", 200_000)
    except Exception:
        pass
    return 200_000


class World:
    """Event-sourced world. apply() = the only mutator; snapshot(now) is
    a pure function of (applied state, file overlay, now)."""

    def __init__(self, root):
        self.root = root
        self.units = {}            # id -> unit dict (heroes + minions)
        self.buildings = {b: {"id": b, "name": n, "activity": 0}
                          for b, n in BUILDINGS}
        self.resources = {"gold": 0, "calls": 0}
        self.regions = {}          # name -> {revealed, activity, lanes, files}
        self.workers = []          # recent hook firings: {ts, hook, tool}
        self.worker_total = 0
        self.goal = None           # main quest text (latest goal intent)
        self.orders = {}           # unit id -> queued order dicts
        self._class_seq = {}
        self._window = default_window(root)
        self._submodel = "swe-2-max"
        try:
            with open(os.path.join(root, "data", "bundle-models.json"),
                      encoding="utf-8") as f:
                self._submodel = json.load(f).get(
                    "default_subagent_model", self._submodel)
        except Exception:
            pass
        self._thresholds = load_thresholds(root)
        self._live = {}            # unit id -> last computed live status

    # ---- event application (only path that mutates state) ----

    def apply(self, ev):
        ts = ev.get("ts", time.time())
        et = ev.get("type", "")
        if et.startswith("hook."):
            self._apply_hook(ev, ts)
        elif et == "intent.created":
            self._apply_intent(ev.get("intent") or {}, ts)
        elif et == "decision.created":
            self._bump("town-hall", ts)
        elif et == "decision.answered":
            self._bump("town-hall", ts)

    def _bump(self, building, ts):
        if building in self.buildings:
            self.buildings[building]["activity"] += 1

    def _touch_path(self, path, lane, ts):
        reg = region_of(self.root, path)
        if not reg:
            return
        r = self.regions.setdefault(reg, {"id": reg, "revealed": False,
                                          "activity": 0, "lanes": {},
                                          "files": {}})
        r["revealed"] = True
        r["activity"] += 1
        r["lanes"][lane] = r["lanes"].get(lane, 0) + 1
        f = r["files"].setdefault(path, set())
        f.add(lane)

    def _apply_hook(self, ev, ts):
        tool = ev.get("tool") or ""
        payload = ev.get("payload") or {}
        ti = payload.get("tool_input") or {}
        resp = payload.get("tool_response", payload.get("tool_output",
                                payload.get("result")))
        lane = str(ti.get("lane") or payload.get("session_id") or "cmdr")
        self.worker_total += 1
        self.workers.append({"ts": ts, "hook": ev.get("hook", ""),
                             "tool": tool})
        if len(self.workers) > 64:
            self.workers = self.workers[-64:]
        if ev.get("hook") == "PostToolUse" and tool:
            out = _output_text(payload)
            self.resources["gold"] += len(out) // CHARS_PER_TOKEN
            self.resources["calls"] += 1
            b = TOOL_TO_BUILDING.get(tool)
            if b:
                self._bump(b, ts)
        if tool in FILE_TOOLS:
            p = _input_path(ti)
            if p:
                self._touch_path(p, lane, ts)
        if tool == "run_subagent":
            self._spawn_hero(ti, resp, ts)
        elif tool == "read_subagent":
            self._debrief_hero(ti, resp, ts)
        elif tool == "exec" and isinstance(resp, dict):
            sid = resp.get("shell_id") or resp.get("id")
            if sid:
                self._spawn_minion(str(sid), lane, ts)
        elif tool in ("get_output", "write_to_process"):
            sid = ti.get("shell_id")
            if sid and ("sh-" + str(sid)) in self.units:
                self.units["sh-" + str(sid)]["last_seen"] = ts
        elif tool == "kill_shell":
            sid = ti.get("shell_id")
            self.units.pop("sh-" + str(sid), None)

    def _spawn_hero(self, ti, resp, ts):
        aid = _agent_id(resp) or "fg-%d" % int(ts * 1000)
        profile = str(ti.get("profile") or "?")
        cls = HERO_CLASSES.get(profile, "Squire")
        self._class_seq[cls] = self._class_seq.get(cls, 0) + 1
        self.units[aid] = {
            "id": aid, "kind": "hero", "profile": profile, "cls": cls,
            "name": "%s-%d" % (cls, self._class_seq[cls]),
            "model": self._submodel,
            "lane": str(ti.get("lane") or ""),
            "task": (ti.get("task") or "")[:120],
            "title": ti.get("title", ""),
            "status": "running" if ti.get("is_background") else "done",
            "spawned_at": ts, "last_seen": ts,
            "xp": 0, "level": 1, "orders": [], "inventory": [],
        }

    def _debrief_hero(self, ti, resp, ts):
        aid = str(ti.get("agent_id", ""))
        u = self.units.get(aid)
        if not u:
            return
        txt = resp if isinstance(resp, str) else json.dumps(resp or "")
        low = txt.lower()
        u["status"] = "failed" if ("failed" in low or "error" in low) \
            else "done"
        u["last_seen"] = ts
        u["xp"] = u.get("xp", 0) + 1
        u["level"] = 1 + u["xp"] // 3

    def _spawn_minion(self, sid, lane, ts):
        uid = "sh-" + sid
        self.units[uid] = {"id": uid, "kind": "minion", "cls": "Minion",
                           "name": "Shell-" + sid[-4:],
                           "summoner": lane, "lane": lane,
                           "status": "running", "spawned_at": ts,
                           "last_seen": ts, "ttl": MINION_TTL_S}

    def _apply_intent(self, it, ts):
        kind = it.get("kind")
        if kind == "goal":
            self.goal = {"text": it.get("text", ""), "ts": ts}
        elif kind == "order" and it.get("to"):
            self.orders.setdefault(str(it["to"]), []).append(it)

    # ---- time-derived live state ----

    def _live_status(self, u, now):
        if u["kind"] != "hero" or u["status"] in ("done", "failed"):
            return u["status"]
        idle_for = now - u.get("last_seen", now)
        if idle_for > STALE_AFTER_S:
            return "stale"
        if idle_for > IDLE_AFTER_S:
            return "idle"
        return u["status"]

    def tick(self, now):
        """Compute live statuses; expire minions. Returns delta dict for
        broadcast (empty dict = nothing changed)."""
        deltas = {}
        for uid, u in list(self.units.items()):
            if u["kind"] == "minion" and \
                    now - u.get("last_seen", now) > u.get("ttl", MINION_TTL_S):
                del self.units[uid]
                deltas[uid] = {"expired": True}
                continue
            live = self._live_status(u, now)
            if self._live.get(uid) != live:
                self._live[uid] = live
                deltas[uid] = {"status_live": live}
        return deltas

    # ---- snapshot ----

    def _region_list(self):
        out = []
        for r in self.regions.values():
            contested = sum(1 for lanes in r["files"].values()
                            if len(lanes) > 1)
            out.append({"id": r["id"], "revealed": r["revealed"],
                        "activity": r["activity"],
                        "lanes": sorted(r["lanes"]),
                        "contested": contested})
        return sorted(out, key=lambda x: x["id"])

    def _quests(self):
        qs = scan_issues(self.root)
        done = {q["id"] for q in qs
                if q["status"] in ("done", "closed", "complete")}
        for q in qs:
            deps = [d.strip() for d in re.split(r"[,;\s]+",
                    q.get("blocked_by") or "") if d.strip()
                    and d.strip() != "-"]
            q["deps"] = deps
            q["blocked"] = any(d not in done for d in deps)
        if self.goal:
            qs.insert(0, {"id": "main-quest", "effort": "",
                          "title": self.goal["text"], "status": "main",
                          "blocked_by": "", "deps": [], "blocked": False})
        return qs

    def snapshot(self, now=None):
        now = time.time() if now is None else now
        ledgers = scan_ledgers(self.root)
        by_lane = {}
        for lg in ledgers:
            passed = sum(1 for g in lg["gates"] if g["state"] == "pass")
            failed = any(g["state"] == "fail" for g in lg["gates"])
            by_lane[lg["id"]] = {"passed": passed, "failed": failed,
                                 "gates": lg["gates"]}
        # heartbeat overlay: .devin/rts/agents/<key>/status.json files,
        # matched to a hero by id or by contract-id named in task/title
        # (same convention as the v1 fleet projection).
        beats = {}
        adir = os.path.join(self.root, ".devin", "rts", "agents")
        if os.path.isdir(adir):
            for key in sorted(os.listdir(adir)):
                p = os.path.join(adir, key, "status.json")
                try:
                    with open(p, encoding="utf-8") as f:
                        beats[key] = json.load(f)
                except Exception:
                    continue
        units = []
        for u in self.units.values():
            u = dict(u)
            if u["kind"] == "hero":
                u["status_live"] = self._live_status(u, now)
                lane = by_lane.get(u.get("lane") or "")
                if lane:
                    total = len(lane["gates"]) or 1
                    u["hp"] = round(100 * lane["passed"] / total)
                    u["gate_fail"] = lane["failed"]
                    u["xp"] = u.get("xp", 0) + lane["passed"]
                    u["level"] = 1 + u["xp"] // 3
                    u["inventory"] = [
                        {"gate": g["id"], "evidence": g.get("evidence", "")}
                        for g in lane["gates"]
                        if g["state"] == "pass" and g.get("evidence")][:6]
                else:
                    u.setdefault("hp", 100)
                hb = beats.get(u["id"])
                if not hb:
                    for key, beat in beats.items():
                        if key in (u.get("task") or "") or \
                                key in (u.get("title") or ""):
                            hb = beat
                            break
                if hb:
                    u["heartbeat"] = hb
                    u["bark"] = hb.get("note") or None
                    if isinstance(hb.get("pct"), (int, float)):
                        u["hp"] = max(0, min(100, round(hb["pct"])))
                    ctx = hb.get("ctx", hb.get("context_pct"))
                    u["mana"] = (max(0, min(100, 100 - ctx))
                                 if isinstance(ctx, (int, float)) else None)
                else:
                    u["mana"] = None
                u["orders"] = self.orders.get(u["id"], [])
            units.append(u)
        # gold = est tokens spent = tool-output tokens + 200/call overhead
        # (same accounting as scripts/context-pressure.py)
        gold = self.resources["gold"] + self.resources["calls"] * 200
        lumber_pct = round(100.0 * gold / self._window, 2) if self._window else 0
        w, c, clr = self._thresholds
        upkeep = ("clear-now" if lumber_pct >= clr else
                  "high" if lumber_pct >= c else
                  "low" if lumber_pct >= w else "none")
        supply_used = sum(1 for u in self.units.values()
                          if u["kind"] == "hero"
                          and self._live_status(u, now) in ("running", "idle"))
        workers = [wk for wk in self.workers
                   if now - wk["ts"] <= WORKER_WINDOW_S]
        return {
            "now": now,
            "units": units,
            "buildings": list(self.buildings.values()),
            "resources": {"gold": gold, "lumber_pct": lumber_pct,
                          "supply_used": supply_used,
                          "supply_cap": SUPPLY_CAP, "upkeep": upkeep,
                          "window": self._window},
            "quests": self._quests(),
            "map": {"root": self.root, "regions": self._region_list(),
                    "workers_active": len(workers),
                    "workers_total": self.worker_total},
        }

    @classmethod
    def replay(cls, root, events, now=None):
        w = cls(root)
        for ev in events:
            w.apply(ev)
        return w

    @classmethod
    def replay_file(cls, root, path, now=None):
        events = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except ValueError:
                            continue
        except OSError:
            pass
        return cls.replay(root, events, now)
