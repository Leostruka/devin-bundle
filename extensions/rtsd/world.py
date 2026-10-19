"""world - event-sourced RTS world model for rtsd (GDD:
.devin/scratch/agentcraft-rts-v2/gdd.md).

Purity contract: World.apply(ev) mutates only event-derived state. All
time-derived fields (decay, idle, minion TTL, worker window) are computed
in snapshot(now) from stored timestamps, so replaying events.jsonl with
the same `now` reproduces an identical world dict. Stdlib only.
"""
import math
import os
import re
import json
import subprocess
import time

CHARS_PER_TOKEN = 4
SUPPLY_CAP = 8          # concurrent-hero design cap (GDD supply/food)
WORKER_WINDOW_S = 60.0  # a hook firing keeps a peasant alive this long
MINION_TTL_S = 300.0    # a summoned shell unit fades without fresh signals
IDLE_AFTER_S = 120.0    # hero with no events this long reads as idle
STALE_AFTER_S = 600.0   # beyond this the hero is stale (signal lost)

MAP_W, MAP_H = 72, 54   # tile grid shared with web/js/engine.js
LIT_WINDOW_S = 180.0    # lit tile re-dims to explored after this quiet period
REVEAL_RADIUS = 1       # a file touch lights a 3x3 tile patch
GOLD_NODES = 8          # largest files become resource nodes
_SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__",
              ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv",
              "venv", "dist", "build"}
# per-tile mark codes in snapshot map.mark
M_NONE, M_PLOT, M_CONTESTED, M_QUEST, M_GOLD, M_CAMP = range(6)

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

# Preferred home region per building (falls back round-robin when the
# workspace lacks it or its plots are full).
BUILDING_AFFINITY = {
    "town-hall": "root", "watchtower": "root",
    "library": ".devin", "trophy-hall": ".devin",
    "barracks": "agents", "tavern": "agents",
    "runeforge": "scripts", "vault": "docs",
    "portal": "extensions", "marketplace": "extensions",
    "altar": "tests",
}


def assign_sites(layout):
    """Pin each building to a fixed map plot: affinity region first, then
    round-robin over remaining plots. Deterministic per layout."""
    plots = layout["plots"]
    regs = layout["regions"]
    used = set()
    sites = {}

    def take(r):
        for pi, xy in enumerate(plots.get(r, [])):
            if (r, pi) not in used:
                used.add((r, pi))
                return {"region": r, "plot": pi, "xy": list(xy)}
        return None

    deferred = []
    for bid, _name in BUILDINGS:
        pref = BUILDING_AFFINITY.get(bid)
        s = take(pref) if pref in plots else None
        if s:
            sites[bid] = s
        else:
            deferred.append(bid)
    ri = 0
    for bid in deferred:
        for k in range(len(regs)):
            s = take(regs[(ri + k) % len(regs)])
            if s:
                sites[bid] = s
                ri = ri + k + 1
                break
        else:                     # more buildings than plots: overflow
            r = regs[ri % len(regs)]
            cx, cy = layout["capitals"][r]
            sites[bid] = {"region": r, "plot": -1, "xy": [cx, cy]}
            ri += 1
    return sites

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


def _h32(s):
    """FNV-1a; deterministic across processes (unlike builtin hash())."""
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _scan_root(root):
    """Top-level dirs -> regions; walk (bounded) -> file counts + sizes."""
    dirs, counts, sizes = [], {}, []
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return ["root"], {"root": 0}, []
    for name in names:
        p = os.path.join(root, name)
        if os.path.isdir(p) and name not in _SKIP_DIRS:
            dirs.append(name)
    regions = dirs + ["root"]
    counts = {r: 0 for r in regions}
    walked = 0
    for base, dnames, fnames in os.walk(root):
        dnames[:] = [d for d in dnames if d not in _SKIP_DIRS]
        rel = os.path.relpath(base, root).replace("\\", "/")
        top = "root" if rel == "." else rel.split("/")[0]
        if top not in counts:
            top = "root"
        for fn in fnames:
            p = os.path.join(base, fn)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            counts[top] += 1
            sizes.append((sz, p))
            walked += 1
        if walked > 20000:
            break
    return regions, counts, sizes


def build_layout(root):
    """Static terrain for this workspace: region set from top-level dirs,
    capitals on a deterministic ring, tiles assigned by weighted Voronoi
    (bigger dirs -> bigger territory), fixed build plots + gold nodes."""
    regions, counts, sizes = _scan_root(root)
    n = len(regions)
    cx0, cy0 = MAP_W / 2.0, MAP_H / 2.0
    rx, ry = MAP_W * 0.36, MAP_H * 0.36
    phase = (_h32(os.path.abspath(root)) % 628) / 100.0
    caps = {}
    for i, r in enumerate(regions):
        ang = phase + 6.2831853 * i / n
        caps[r] = [int(cx0 + rx * math.cos(ang)),
                   int(cy0 + ry * math.sin(ang))]
    weight = {r: 1.0 + 0.6 * math.log10(1 + counts.get(r, 0))
              for r in regions}
    tile_region = [0] * (MAP_W * MAP_H)
    regtiles = {r: [] for r in regions}
    for y in range(MAP_H):
        for x in range(MAP_W):
            bi, bs = 0, 1e30
            for i, r in enumerate(regions):
                cx, cy = caps[r]
                d2 = (x - cx) * (x - cx) + (y - cy) * (y - cy)
                s = d2 / weight[r]
                if s < bs:
                    bs, bi = s, i
            i0 = y * MAP_W + x
            tile_region[i0] = bi
            regtiles[regions[bi]].append(i0)
    plots = {}
    for r in regions:
        cx, cy = caps[r]
        tiles = regtiles[r] or [cy * MAP_W + cx]
        alt = tiles[_h32(r + ":plot") % len(tiles)]
        plots[r] = [[cx, cy], [alt % MAP_W, alt // MAP_W]]
    gold = sorted(sizes, reverse=True)[:GOLD_NODES]
    layout = {"sig": _h32(",".join(regions)), "w": MAP_W, "h": MAP_H,
              "regions": regions, "counts": counts, "capitals": caps,
              "tile_region": tile_region, "plots": plots,
              "gold": [{"path": p, "size": s} for s, p in gold]}
    layout["_regtiles"] = regtiles
    return layout


def file_tile(layout, root, path):
    """Deterministic tile for a file inside its region's tile set."""
    reg = region_of(root, path)
    tiles = layout["_regtiles"].get(reg) or layout["_regtiles"]["root"]
    return tiles[_h32(path) % len(tiles)]


# Kit vocabulary from the GDD: ability flags derived from the profile's
# real allowed-tools (agents/<profile>.md text).
_KIT_TOOLS = {
    "Write": ("write", "edit", "notebook_edit"),
    "March": ("exec", "get_output", "write_to_process", "kill_shell"),
    "Cartography": ("read", "grep", "glob", "find_file_by_name"),
    "Farsight": ("web_search", "webfetch"),
    "Envoy": ("mcp_",),
    "Parley": ("ask_user_question",),
    "Camp": ("todo_write",),
}


def _profile_sheet(root, profile):
    for base in (os.path.join(root, "agents"),
                 os.path.join(root, ".devin", "agents")):
        p = os.path.join(base, profile + ".md")
        if os.path.isfile(p):
            try:
                return open(p, encoding="utf-8").read()
            except OSError:
                return ""
    return ""


def profile_kit(root, profile):
    """Ability names whose backing tools appear in the profile sheet;
    'Verify' replaces 'March' when exec is restricted to read-only/tests."""
    text = _profile_sheet(root, profile).lower()
    if not text:
        return ["Cartography"]   # unknown profile -> read-only squire kit
    kit = []
    for name, tools in _KIT_TOOLS.items():
        if any(t in text for t in tools):
            kit.append(name)
    if "March" in kit and re.search(r"read-only|verify only|never edit",
                                  text):
        kit[kit.index("March")] = "Verify"
    return kit


def profile_model(root, profile):
    """Model id pinned in the profile's frontmatter (`model: swe-2-*`),
    else None (falls back to the config subagent pin)."""
    text = _profile_sheet(root, profile)
    m = re.search(r"^model:\s*([A-Za-z0-9_.-]+)", text, re.M)
    return m.group(1) if m else None


# model effort -> unit tier badge (GDD: Medium=Footman, High=Commander,
# Max=Knight); resolved from data/bundle-models.json, not hardcoded ids
def model_tier(root, model_id):
    """Tier badge for a model id per data/bundle-models.json effort."""
    try:
        with open(os.path.join(root, "data", "bundle-models.json"),
                  encoding="utf-8") as f:
            for m in json.load(f).get("models", []):
                if m.get("id") == model_id:
                    return {"medium": "Footman", "high": "Commander",
                            "max": "Knight"}.get(m.get("effort"))
    except Exception:
        pass
    return None


def config_subagent_model(root):
    """`agent.subagent_model` from config.json (the Armory pin); None when
    the key is absent so callers fall back to the registry default."""
    try:
        with open(os.path.join(root, "config.json"),
                  encoding="utf-8") as f:
            cfg = json.load(f)
        return (cfg.get("agent") or {}).get("subagent_model")
    except Exception:
        return None


def profile_tier(root, profile):
    """Model tier from TOOLS-MAP (Medium->Footman, Max->Knight)."""
    tm = os.path.join(root, ".devin", "docs", "TOOLS-MAP.md")
    try:
        for ln in open(tm, encoding="utf-8"):
            m = re.match(r"\|\s*`?" + re.escape(profile) +
                         r"`?\s*\|\s*\w+\s*\|\s*(Medium|Max|High)", ln)
            if m:
                return "Knight" if m.group(1) != "Medium" else "Footman"
    except OSError:
        pass
    return "Footman"


# ---- spellbook / tech tree (#132) ----
# School grouping from GDD 1.4 (the 83-spell, 6-school table). The spell
# list itself always comes from the real skills/ dir scan: names on disk
# that the GDD table does not place land in "Unsorted" so no real skill is
# hidden and none are invented.
SKILL_SCHOOLS = {
    "Command": ["ask-bundle", "dispatching-parallel-agents", "execution",
                "gates", "grilling", "handoff", "intake", "learn-mode",
                "planning", "playbook", "project-orchestrator",
                "scheduled-turns", "skill-discovery", "wizard"],
    "War": ["firmware-probe", "mobile-probe", "net-probe", "re-binary",
            "red-team", "scan", "web-probe", "wireless-probe"],
    "Lore": ["ai-coding-dictionary", "ai-tools", "context-hygiene",
             "context7", "data-analyst", "fact-check", "jira",
             "knowledge-modeling", "memory-management",
             "obsidian-workflow", "research", "wait-what"],
    "Craft": ["a11y-audit", "api-spec", "architecture",
              "architecture-diagrams", "brag", "code-review", "database",
              "debugging", "deploy", "devin-config", "docker",
              "e2e-testing", "finishing-a-development-branch", "gh",
              "git-workflows", "i18n", "impeccable",
              "observability-quality", "performance", "pr",
              "project-bootstrap", "prompt-compiler", "prototype",
              "retro", "security", "self-improvement", "setup-pre-commit",
              "teach", "testing", "writing-skills"],
    "Creation": ["ai3d-gen", "animation-direction", "ascii-art",
                 "creative-engineering", "humanizer", "image-forensics",
                 "media-tools", "mesh-utils", "operate-blender",
                 "operate-godot", "scrape-tools", "social-midia",
                 "youtube-fetcher", "mcp-governance"],
    "Summoning": ["computer-use", "cu-realtime", "implement-laya",
                  "laya-orchestrator", "system-control"],
}


def scan_skills(root):
    """Real skill names = directories under skills/ (SKILL.md inside)."""
    sdir = os.path.join(root, "skills")
    out = []
    if not os.path.isdir(sdir):
        return out
    for name in sorted(os.listdir(sdir)):
        if os.path.isdir(os.path.join(sdir, name)):
            out.append(name)
    return out


_SKILL_KEYS = ("skill", "name", "skill_name", "id", "query", "args")
_SKILL_VERBS = {"invoke", "list", "search"}


def skill_name_of(ti):
    """Skill name from a `skill` tool_input ({command:'invoke', ...})."""
    if not isinstance(ti, dict):
        return None
    for k in _SKILL_KEYS:
        v = ti.get(k)
        if isinstance(v, str) and v and v not in _SKILL_VERBS:
            return v.lstrip("/").strip() or None
    v = ti.get("command")
    if isinstance(v, str) and v and v not in _SKILL_VERBS:
        return v.lstrip("/").strip() or None
    return None


def tech_tree(root, casts):
    """Spellbook overlay (#132): real skills grouped by school; cast state
    (casts/last_cast) comes from hook.posttooluse events tool=='skill'."""
    known = scan_skills(root)
    placed = {}
    for school, names in SKILL_SCHOOLS.items():
        for n in names:
            placed[n] = school
    schools = [{"id": s, "spells": []} for s in SKILL_SCHOOLS]
    extra = {"id": "Unsorted", "spells": []}
    by_school = {s["id"]: s for s in schools}
    for name in known:
        c = casts.get(name) or {}
        spell = {"name": name,
                 "path": os.path.join("skills", name, "SKILL.md"),
                 "casts": c.get("n", 0),
                 "last_cast": c.get("last")}
        school = placed.get(name)
        (by_school[school]["spells"] if school
         else extra["spells"]).append(spell)
    if extra["spells"]:
        schools.append(extra)
    return schools


def armory(root):
    """Armory ledger (#132): model tiers from data/bundle-models.json and
    the live subagent pin: config.json agent.subagent_model wins (Alt+Enter
    session picks are session-scoped and never persisted, so the pin is
    the honest upgrade state)."""
    tiers, default = [], None
    try:
        with open(os.path.join(root, "data", "bundle-models.json"),
                  encoding="utf-8") as f:
            cfg = json.load(f)
        default = cfg.get("default_subagent_model")
        for m in cfg.get("models", []):
            tiers.append({"id": m.get("id"), "name": m.get("name"),
                          "effort": m.get("effort"),
                          "role": m.get("role"),
                          "window": m.get("context_window"),
                          "cost_tier": m.get("cost_tier")})
    except Exception:
        pass
    pin = config_subagent_model(root)
    return {"subagent_model": pin or default,
            "pin": "config.json agent.subagent_model" if pin
                   else "data/bundle-models.json default",
            "tiers": tiers}


# Memory doctrines (#132): the 8 RAG chunking strategies as Library
# research. in_use is ONLY set when a real artifact proves it (a memory
# script implementing the strategy or memory files it operates on);
# otherwise the doctrine shows as un-researched with empty evidence.
def _memory_sources(root):
    sdir = os.path.join(root, "scripts")
    src = ""
    if os.path.isdir(sdir):
        for fn in sorted(os.listdir(sdir)):
            if fn.startswith("memory-") and fn.endswith(".py"):
                try:
                    src += open(os.path.join(sdir, fn),
                                encoding="utf-8").read()
                except OSError:
                    pass
    mdir = os.path.join(root, ".devin", "memory")
    notes = [fn for fn in os.listdir(mdir)
             if fn.endswith(".md")] if os.path.isdir(mdir) else []
    return src, notes, mdir


def doctrines(root):
    src, notes, mdir = _memory_sources(root)

    def has(pat):
        return bool(re.search(pat, src, re.I))

    def ev_for(pat):
        """scripts/memory-*.py files whose source matches the probe."""
        sdir = os.path.join(root, "scripts")
        if not os.path.isdir(sdir):
            return []
        ev = []
        for fn in sorted(os.listdir(sdir)):
            if not (fn.startswith("memory-") and fn.endswith(".py")):
                continue
            try:
                body = open(os.path.join(sdir, fn),
                            encoding="utf-8").read()
            except OSError:
                continue
            if re.search(pat, body, re.I):
                ev.append(os.path.join("scripts", fn))
        return ev

    found = {}
    # document-level: scripts retrieve whole note files keyed by cues
    doc_ev = [os.path.join("scripts", fn) for fn in
              ("memory-retrieval.py", "memory-post-edit.py")
              if os.path.isfile(os.path.join(root, "scripts", fn))]
    doc_use = bool(doc_ev and notes and has(r"cues?"))
    found["document"] = (doc_use, doc_ev + [
        "%s (%d notes)" % (os.path.join(".devin", "memory"), len(notes))]
        if doc_use else [])
    # hierarchical: a MOC index file over the notes
    moc = os.path.join(mdir, "MOC.md")
    hier = os.path.isfile(moc) and bool(notes)
    found["hierarchical"] = (hier, [os.path.join(
        ".devin", "memory", "MOC.md")] if hier else [])
    probes = {"fixed": r"chunk_?size|fixed.?size",
              # recursive-splitting probe must not trip on glob's
              # `recursive=True` kwarg - require split/chunk context
              "recursive": r"recursive[-_ ]?(split|chunk)",
              "semantic": r"embed|vector|cosine|semantic",
              "llm": r"llm|prompt.*chunk",
              "agentic": r"agentic",
              "late": r"late.?chunk"}
    for did, pat in probes.items():
        ev = ev_for(pat)
        found[did] = (bool(ev), ev)
    labels = [("fixed", "Fixed-size chunking"),
              ("recursive", "Recursive splitting"),
              ("document", "Document-level chunks"),
              ("semantic", "Semantic/embedding chunking"),
              ("llm", "LLM-guided chunking"),
              ("agentic", "Agentic chunking"),
              ("late", "Late chunking"),
              ("hierarchical", "Hierarchical index")]
    return [{"id": did, "label": label,
             "in_use": found[did][0], "evidence": found[did][1]}
            for did, label in labels]


def profile_skills(root, profile):
    """A hero's spellbook = real skills whose names are literally invoked
    in the profile sheet (agents/<profile>.md 'Skills to invoke' etc)."""
    text = _profile_sheet(root, profile).lower()
    if not text:
        return []
    return [n for n in scan_skills(root)
            if re.search(r"`?" + re.escape(n) + r"`?", text)]


def load_layout(root):
    """Persisted map.json keyed by region signature; regenerates when the
    top-level dir set changes (issue #122)."""
    mp = os.path.join(root, ".devin", "rts", "map.json")
    try:
        with open(mp, encoding="utf-8") as f:
            saved = json.load(f)
    except Exception:
        saved = None
    regions = _scan_root(root)[0]
    if saved and saved.get("sig") == _h32(",".join(regions)) \
            and saved.get("w") == MAP_W and saved.get("h") == MAP_H:
        regtiles = {r: [] for r in saved["regions"]}
        for i, ri in enumerate(saved["tile_region"]):
            regtiles[saved["regions"][ri]].append(i)
        saved["_regtiles"] = regtiles
        return saved
    layout = build_layout(root)
    try:
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        out = {k: v for k, v in layout.items() if not k.startswith("_")}
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(out, f)
    except OSError:
        pass
    return layout


class World:
    """Event-sourced world. apply() = the only mutator; snapshot(now) is
    a pure function of (applied state, file overlay, now)."""

    def __init__(self, root):
        self.root = root
        self.units = {}            # id -> unit dict (heroes + minions)
        self.buildings = {b: {"id": b, "name": n, "activity": 0}
                          for b, n in BUILDINGS}
        self.resources = {"gold": 0, "calls": 0}
        self.gold_log = []         # [{ts,amt,lane}] income history (#131)
        self.burn = {}             # lane -> est tokens spent (#131)
        self.burn_calls = {}       # lane -> tool call count (#131)
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
        # #132 Armory: config.json agent.subagent_model pins the live
        # subagent model over the registry default
        pin = config_subagent_model(root)
        if pin:
            self._submodel = pin
        self.skill_casts = {}      # skill name -> {n, last} (#132)
        self._thresholds = load_thresholds(root)
        self._live = {}            # unit id -> last computed live status
        self.layout = load_layout(root)   # static terrain (map.json)
        self.sites = assign_sites(self.layout)  # building -> plot
        self.tile_heat = {}        # tile idx -> last file-touch ts
        self.tile_of = {}          # path -> tile idx (deterministic)
        self.file_lanes = {}       # path -> set(lanes) for contested
        self._fogc = {}            # tile idx -> last broadcast fog level
        self.feed = []             # comms chatter lines (#128, event-sourced)
        self.mail = []             # mailbox deposits seen via events
        self.mail_seen = set()     # msg ids already announced
        self.dec_seen = set()      # decision ids already announced (#129)
        self.notes = {}            # agent key -> last status.json note
        self._fn = 0               # feed-line counter (template pick, replay-
                                   # deterministic: same order, same count)
        # WC3 start: home territory around the "root" capital is explored
        # (ts=0 -> permanently dim-explored, never lit)
        hc = self.layout["capitals"].get("root")
        if hc:
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, ny = hc[0] + dx, hc[1] + dy
                    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                        self.tile_heat.setdefault(ny * MAP_W + nx, 0.0)

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
            self.dec_seen.add(str((ev.get("payload") or {})
                                  .get("id") or ""))
        elif et == "decision.answered":
            self._bump("town-hall", ts)
            self.dec_seen.discard(str(ev.get("id") or ""))
        elif et == "mail.deposit":
            m = ev.get("mail") or {}
            if m.get("id") and m["id"] not in self.mail_seen:
                self.mail_seen.add(m["id"])
                self.mail.append(dict(m))
                if len(self.mail) > 64:
                    self.mail = self.mail[-64:]
        elif et == "agent.note":
            key = ev.get("agent")
            if key:
                self.notes[str(key)] = ev.get("note", "")
        line = self.feed_line(ev, ts)
        if line:
            self.feed.append(line)
            self._fn += 1
            if len(self.feed) > 400:
                self.feed = self.feed[-400:]
        return line

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
        # tile-level fog: light the file's tile + reveal radius (#122)
        t = self.tile_of.get(path)
        if t is None:
            t = file_tile(self.layout, self.root, path)
            self.tile_of[path] = t
        self.file_lanes.setdefault(path, set()).add(lane)
        x, y = t % MAP_W, t // MAP_W
        for dy in range(-REVEAL_RADIUS, REVEAL_RADIUS + 1):
            for dx in range(-REVEAL_RADIUS, REVEAL_RADIUS + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                    self.tile_heat[ny * MAP_W + nx] = ts

    def _apply_hook(self, ev, ts):
        tool = ev.get("tool") or ""
        payload = ev.get("payload") or {}
        ti = payload.get("tool_input") or {}
        resp = payload.get("tool_response", payload.get("tool_output",
                                payload.get("result")))
        lane = str(ti.get("lane") or payload.get("session_id") or "cmdr")
        self.worker_total += 1
        # peasant scurries: previous destination -> this tool's building
        # site (or the touched file's region capital for FILE_TOOLS) (#125)
        p = _input_path(ti) if tool in FILE_TOOLS else None
        if p:
            t = file_tile(self.layout, self.root, p)
            to = [t % MAP_W, t // MAP_W]
        else:
            to = (self.sites.get(TOOL_TO_BUILDING.get(tool, "town-hall"))
                  or self.sites["town-hall"])["xy"]
        frm = (self.workers[-1]["to"] if self.workers
               else self.sites["town-hall"]["xy"])
        self.workers.append({"ts": ts, "hook": ev.get("hook", ""),
                             "tool": tool, "from": frm, "to": list(to)})
        if len(self.workers) > 64:
            self.workers = self.workers[-64:]
        if ev.get("hook") == "PostToolUse" and tool:
            out = _output_text(payload)
            self.resources["gold"] += len(out) // CHARS_PER_TOKEN
            self.resources["calls"] += 1
            # #131 economy: per-event income record (output tokens + the
            # same 200/call overhead used for gold) attributed to the
            # event lane so heroes show their own context burn
            amt = len(out) // CHARS_PER_TOKEN + 200
            self.gold_log.append({"ts": ts, "amt": amt, "lane": lane})
            if len(self.gold_log) > 100:
                self.gold_log = self.gold_log[-100:]
            self.burn[lane] = self.burn.get(lane, 0) + amt
            self.burn_calls[lane] = self.burn_calls.get(lane, 0) + 1
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
        elif tool == "skill":                    # #132: spell cast
            nm = skill_name_of(ti)
            if nm:
                c = self.skill_casts.setdefault(nm, {"n": 0, "last": 0})
                c["n"] += 1
                c["last"] = ts

    def _spawn_hero(self, ti, resp, ts):
        aid = _agent_id(resp) or "fg-%d" % int(ts * 1000)
        profile = str(ti.get("profile") or "?")
        cls = HERO_CLASSES.get(profile, "Squire")
        self._class_seq[cls] = self._class_seq.get(cls, 0) + 1
        # barracks rally point: the newest set_rally order routes the next
        # spawn's lane to the rally region (#127)
        lane = str(ti.get("lane") or "")
        rally = self.rally_of("barracks")
        if rally and rally.get("region"):
            lane = rally["region"]
        self.units[aid] = {
            "id": aid, "kind": "hero", "profile": profile, "cls": cls,
            "name": "%s-%d" % (cls, self._class_seq[cls]),
            # model = the hero's own profile pin (agents/<p>.md `model:`),
            # else the config/registry subagent pin (#132 armory tier)
            "model": profile_model(self.root, profile) or self._submodel,
            # tier badge follows the resolved model's registry effort;
            # TOOLS-MAP is the fallback when the model id is unknown
            "tier": model_tier(self.root, profile_model(self.root, profile)
                               or self._submodel)
                    or profile_tier(self.root, profile),
            "kit": profile_kit(self.root, profile),
            "lane": lane,
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

    # ---- orders / rally (#127) ----

    # intent file status -> order lifecycle state; rts-intents.py flips
    # pending -> surfaced/delivered when the session consumes the file.
    _ORDER_STATES = {"pending": "queued", "surfaced": "acknowledged",
                     "delivered": "acknowledged"}

    def _intent_status(self):
        """intent id -> file status, read fresh each snapshot (the intents
        dir is the truth; ghost waypoints key off 'queued')."""
        out = {}
        idir = os.path.join(self.root, ".devin", "rts", "intents")
        if not os.path.isdir(idir):
            return out
        for fn in os.listdir(idir):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(idir, fn),
                          encoding="utf-8") as f:
                    it = json.load(f)
            except Exception:
                continue
            if isinstance(it, dict) and it.get("id"):
                out[str(it["id"])] = it.get("status", "pending")
        return out

    def _order_view(self, it, istatus):
        """Snapshot view of one queued order: adds lifecycle state."""
        o = dict(it)
        o["state"] = self._ORDER_STATES.get(istatus, "consumed")
        return o

    def rally_of(self, bid):
        """Latest set_rally order on a building -> {x,y,region?,id}."""
        for it in reversed(self.orders.get(bid, [])):
            if it.get("order") != "set_rally":
                continue
            r = {"x": it.get("x"), "y": it.get("y"), "id": it.get("id")}
            x, y = it.get("x"), it.get("y")
            if isinstance(x, int) and isinstance(y, int) and \
                    not isinstance(x, bool) and not isinstance(y, bool) and \
                    0 <= x < MAP_W and 0 <= y < MAP_H:
                ri = self.layout["tile_region"][y * MAP_W + x]
                r["region"] = self.layout["regions"][ri]
            if it.get("channel"):
                r["channel"] = it["channel"]
            return r
        return None

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
        # tile fog demotions (lit -> explored) ride the tick broadcast
        fdiff = {}
        for t, hts in self.tile_heat.items():
            lvl = 2 if now - hts < LIT_WINDOW_S else 1
            if self._fogc.get(t, 0) != lvl:
                self._fogc[t] = lvl
                fdiff[t] = lvl
        if fdiff:
            deltas["_map"] = {"fog": fdiff}
        return deltas

    # ---- snapshot ----

    def _region_list(self):
        out = []
        caps = self.layout["capitals"]
        plots = self.layout["plots"]
        for rid in self.layout["regions"]:
            r = self.regions.get(rid, {"id": rid, "revealed": False,
                                       "activity": 0, "lanes": {},
                                       "files": {}})
            contested = sum(1 for lanes in r["files"].values()
                            if len(lanes) > 1)
            out.append({"id": rid, "revealed": r["revealed"],
                        "activity": r["activity"],
                        "lanes": sorted(r["lanes"]),
                        "contested": contested,
                        "owner": (max(r["lanes"], key=r["lanes"].get)
                                  if r["lanes"] else None),
                        "capital": caps.get(rid),
                        "plots": plots.get(rid, []),
                        "files": self.layout["counts"].get(rid, 0)})
        return out

    def _fog_mark(self, now, by_lane=None):
        """Per-tile fog (0 shroud / 1 explored / 2 lit) + mark codes.
        Fog is time-derived from tile_heat so replay stays pure."""
        n = MAP_W * MAP_H
        fog = [0] * n
        mark = [0] * n
        for t, hts in self.tile_heat.items():
            fog[t] = 2 if now - hts < LIT_WINDOW_S else 1
        for pls in self.layout["plots"].values():
            for x, y in pls:
                mark[y * MAP_W + x] = M_PLOT
        for g in self.layout["gold"]:
            mark[file_tile(self.layout, self.root, g["path"])] = M_GOLD
        for path, lanes in self.file_lanes.items():
            if len(lanes) > 1:      # contested outranks plot/gold marks
                t = self.tile_of.get(path)
                if t is not None:
                    mark[t] = M_CONTESTED
        pois = [{"kind": "gold", "x": file_tile(self.layout, self.root,
                                                g["path"]) % MAP_W,
                 "y": file_tile(self.layout, self.root, g["path"]) // MAP_W,
                 "ref": g["path"], "size": g["size"]}
                for g in self.layout["gold"]]
        for q in self._quests(by_lane):
            if q["kind"] == "main":
                continue
            p = os.path.join(self.root, ".devin", "scratch", q["effort"],
                             "issues", q["id"] + ".md")
            t = file_tile(self.layout, self.root, p)
            if mark[t] == M_NONE:
                mark[t] = M_QUEST
            # marker state for the renderer (#130): done = reward stamp,
            # failed = stays red until retried, blocked = greyed "?",
            # open = golden "!"
            g = q.get("gates")
            qst = ("done" if q["done"] else
                   "failed" if q["failed"] or (g and g["fail"]) else
                   "blocked" if q["blocked"] else "open")
            pois.append({"kind": "quest", "x": t % MAP_W, "y": t // MAP_W,
                         "ref": q["id"], "title": q["title"], "qst": qst})
        caps = self.layout["capitals"]
        for r in self.layout["regions"]:
            live = self.regions.get(r)
            if live and live["activity"]:
                continue
            cx, cy = caps[r]
            if mark[cy * MAP_W + cx] == M_NONE:
                mark[cy * MAP_W + cx] = M_CAMP
            pois.append({"kind": "camp", "x": cx, "y": cy, "ref": r})
        return fog, mark, pois

    def building_detail(self, bid, now=None, extra=None):
        """Per-building real state for the inspector panel (#123). Every
        field is read from an actual bundle/CLI surface - nothing fake."""
        now = time.time() if now is None else now
        extra = extra or {}
        b = self.buildings.get(bid)
        if not b:
            return None
        d = {"id": bid, "name": b["name"], "activity": b["activity"],
             "pos": self.sites.get(bid), "rally": self.rally_of(bid)}
        root = self.root
        if bid == "town-hall":
            qs = self._quests()
            done = {q["id"] for q in qs if q.get("done")}
            d["goal"] = self.goal
            d["quests"] = {"total": len(qs), "done": len(done),
                           "blocked": sum(1 for q in qs if q["blocked"])}
            d["workers"] = {"total": self.worker_total,
                            "active": sum(1 for wk in self.workers
                                          if now - wk["ts"]
                                          <= WORKER_WINDOW_S)}
            d["decisions_pending"] = extra.get("decisions_pending", 0)
        elif bid == "barracks":
            d["classes"] = [{"profile": p, "cls": c,
                             "model": self._submodel}
                            for p, c in sorted(HERO_CLASSES.items())]
            d["queue"] = [i for i in extra.get("intents", [])
                          if i.get("kind") == "spawn"]
        elif bid == "tavern":
            roster = []
            tiers = {}
            tm = os.path.join(root, ".devin", "docs", "TOOLS-MAP.md")
            try:
                for ln in open(tm, encoding="utf-8"):
                    mm = re.match(r"\|\s*`?([a-z_-]+)`?\s*\|\s*\w+\s*\|"
                                  r"\s*(Medium|Max|High)", ln)
                    if mm:
                        tiers[mm.group(1)] = mm.group(2)
            except OSError:
                pass
            for adir, scope in ((os.path.join(root, "agents"), "user"),
                                (os.path.join(root, ".devin", "agents"),
                                 "project")):
                if not os.path.isdir(adir):
                    continue
                for fn in sorted(os.listdir(adir)):
                    if fn.endswith(".md") and fn != "README.md":
                        p = fn[:-3]
                        roster.append({"profile": p, "scope": scope,
                                       "cls": HERO_CLASSES.get(p, "Squire"),
                                       "tier": tiers.get(p, "-")})
            d["roster"] = roster
        elif bid == "library":
            mem = os.path.join(root, ".devin", "memory")
            d["entries"] = [
                {"file": fn, "size": os.path.getsize(
                    os.path.join(mem, fn))}
                for fn in sorted(os.listdir(mem))
                if os.path.isfile(os.path.join(mem, fn))
            ] if os.path.isdir(mem) else []
            # #132: tech tree + doctrines read the same real surfaces as
            # the spellbook overlay (skills/, memory scripts)
            d["spellbook"] = tech_tree(root, self.skill_casts)
            d["doctrines"] = doctrines(root)
            d["armory"] = armory(root)
        elif bid == "watchtower":
            lgs = []
            for lg in scan_ledgers(root):
                st = [g["state"] for g in lg["gates"]]
                lgs.append({"id": lg["id"], "pass": st.count("pass"),
                            "fail": st.count("fail"),
                            "pending": st.count("pending")})
            d["ledgers"] = lgs
            adir = os.path.join(root, ".devin", "rts", "agents")
            d["heartbeats"] = len(os.listdir(adir)) \
                if os.path.isdir(adir) else 0
        elif bid == "runeforge":
            sdir = os.path.join(root, "scripts")
            d["artifacts"] = [fn for fn in sorted(os.listdir(sdir))
                              if os.path.isfile(os.path.join(sdir, fn))
                              and re.search(r"prompt|compile|forge|emit|rag",
                                            fn)] \
                if os.path.isdir(sdir) else []
        elif bid == "vault":
            try:
                out = subprocess.run(
                    ["git", "log", "--oneline", "-10"], cwd=root,
                    capture_output=True, text=True, timeout=3)
                d["deposits"] = [l for l in out.stdout.splitlines() if l]
            except Exception:
                d["deposits"] = []
        elif bid == "portal":
            r = dict(extra.get("remote") or {})
            if r.get("opened_at"):
                r["ttl_left_s"] = max(0, int(r["ttl_s"]
                                         - (now - r["opened_at"])))
                r["token"] = bool(r.get("token"))   # never expose the token
            d["remote"] = r
        elif bid == "marketplace":
            cfg = {}
            try:
                with open(os.path.join(root, "data",
                                       "bundle-integrations.json"),
                          encoding="utf-8") as f:
                    cfg = json.load(f).get("mcp", {})
            except Exception:
                pass
            d["servers"] = [{"name": k, "enabled": bool(v.get("enabled")),
                             "transport": v.get("transport", "?")}
                            for k, v in sorted(cfg.items())]
        elif bid == "altar":
            d["fallen"] = [{"id": u["id"], "cls": u.get("cls"),
                            "name": u.get("name"), "profile":
                            u.get("profile"), "task": u.get("task", "")}
                           for u in self.units.values()
                           if u["kind"] == "hero" and u["status"]
                           == "failed"]
        elif bid == "trophy-hall":
            loot = []
            for lg in scan_ledgers(root):
                for g in lg["gates"]:
                    if g["state"] == "pass" and g.get("evidence"):
                        loot.append({"ledger": lg["id"], "gate": g["id"],
                                     "evidence": g["evidence"]})
            d["loot"] = loot[:20]
        return d

    # ---- comms feed (#128) ----
    # Every line is generated inside apply() from the event's real payload,
    # so replaying events.jsonl rebuilds identical scrollback. Template
    # choice uses self._fn (a pure function of event order), never random.

    def _name_of(self, ref):
        """Unit display name for an agent id / unit name / raw handle."""
        if not ref:
            return None
        ref = str(ref)
        u = self.units.get(ref)
        if u:
            return u.get("name") or ref
        for u in self.units.values():
            if u.get("name") == ref:
                return ref
        return None

    def _uid_of(self, ref):
        if not ref:
            return None
        ref = str(ref)
        if ref in self.units:
            return ref
        for uid, u in self.units.items():
            if u.get("name") == ref:
                return uid
        return None

    def _lane_speaker(self, lane):
        """Most recently active hero working this lane, else the peasants."""
        best, bts = None, -1
        for u in self.units.values():
            if u.get("kind") == "hero" and u.get("lane") == lane \
                    and u.get("last_seen", 0) > bts:
                best, bts = u, u["last_seen"]
        if best:
            return best["id"], best.get("name") or best["id"], \
                best.get("cls")
        return None, "Peasants", "Worker"

    def _line(self, ts, kind, who, cls, uid, text):
        return {"t": ts, "kind": kind, "who": who, "cls": cls,
                "uid": uid, "text": text[:160]}

    def feed_line(self, ev, ts):
        """One in-fiction radio line for an event, or None if the event is
        not chatter-worthy. All payloads come from the event itself."""
        et = ev.get("type", "")
        pick = self._fn % 3   # rotates templates deterministically
        if et == "hook.posttooluse":
            tool = ev.get("tool") or ""
            payload = ev.get("payload") or {}
            ti = payload.get("tool_input") or {}
            resp = payload.get("tool_response",
                              payload.get("tool_output",
                                          payload.get("result")))
            if tool == "run_subagent":
                aid = _agent_id(resp)
                uid, name, cls = aid, self._name_of(aid), None
                u = self.units.get(aid) or {}
                cls = u.get("cls")
                return self._line(ts, "spawn", name or "Barracks", cls,
                                  uid, "%s takes the field - %s" % (
                                      name or "new unit",
                                      str(ti.get("task") or "?")[:60]))
            if tool == "read_subagent":
                aid = str(ti.get("agent_id", ""))
                u = self.units.get(aid) or {}
                name = u.get("name") or aid or "?"
                txt = resp if isinstance(resp, str) else json.dumps(
                    resp or "")
                fail = "failed" in txt.lower() or "error" in txt.lower()
                m = re.search(r"(\d+)\s*/\s*(\d+)", txt)
                tail = " - tests %s/%s" % (m.group(1), m.group(2)) if m \
                    else ""
                verb = ("mission failed", "retreat sounded",
                        "unit down")[pick] if fail else \
                    ("area clear", "mission complete",
                     "objective secured")[pick]
                return self._line(ts, "debrief", name, u.get("cls"), aid,
                                  "%s%s" % (verb, tail))
            if tool in FILE_TOOLS:
                p = _input_path(ti)
                if not p:
                    return None
                lane = str(ti.get("lane") or payload.get("session_id")
                           or "cmdr")
                uid, name, cls = self._lane_speaker(lane)
                rel = os.path.relpath(p, self.root).replace("\\", "/") \
                    if os.path.isabs(p) else p
                verb = {"read": "scouting", "grep": "searching",
                        "glob": "mapping", "find_file_by_name": "locating",
                        "write": "raising", "edit": "fortifying",
                        "notebook_edit": "inscribing",
                        "apply_patch": "patching"}.get(tool, "at")
                return self._line(ts, "position", name, cls, uid,
                                  "%s %s" % (verb, rel[-70:]))
            if tool == "exec":
                sid = (resp or {}).get("shell_id") if isinstance(resp, dict) \
                    else None
                if not sid:
                    return None
                nm = "Shell-" + str(sid)[-4:]
                return self._line(ts, "spawn", nm, "Minion", "sh-" +
                                  str(sid), "%s summoned" % nm)
            if tool == "kill_shell":
                sid = ti.get("shell_id")
                if not sid:
                    return None
                nm = "Shell-" + str(sid)[-4:]
                return self._line(ts, "position", nm, "Minion",
                                  "sh-" + str(sid), "%s dismissed" % nm)
            if tool == "skill":                  # #132: spell cast line
                nm = skill_name_of(ti)
                if not nm:
                    return None
                lane = str(ti.get("lane") or payload.get("session_id")
                           or "cmdr")
                uid, name, cls = self._lane_speaker(lane)
                c = self.skill_casts.get(nm) or {}
                return self._line(ts, "spell", name, cls, uid,
                                  "casts %s%s" % (nm, " x%d" % c["n"]
                                                  if c.get("n", 0) > 1
                                                  else ""))
            if tool in ("get_output", "write_to_process"):
                sid = ti.get("shell_id")
                if sid and ("sh-" + str(sid)) in self.units:
                    nm = "Shell-" + str(sid)[-4:]
                    return self._line(ts, "position", nm, "Minion",
                                      "sh-" + str(sid),
                                      "%s reporting in" % nm)
            return None
        if et == "decision.created":
            payload = ev.get("payload") or {}
            kind = payload.get("kind", "decision")
            req = payload.get("requester")
            who = self._name_of(req) if req else None
            return self._line(ts, "council", "War Council", "Marshal",
                              None, "council called - %s awaits ruling%s"
                              % (kind, " (%s)" % who if who else ""))
        if et == "decision.answered":
            return self._line(ts, "council", "War Council", "Marshal",
                              None, "order confirmed - council adjourned")
        if et == "intent.created":
            it = ev.get("intent") or {}
            kind = it.get("kind")
            if kind == "message":
                to = str(it.get("to") or "session")
                nm = self._name_of(to) or to
                return self._line(ts, "steering", "Cmdr", None,
                                  self._uid_of(to),
                                  "-> %s: %s" % (nm, str(
                                      it.get("text") or "")[:80]))
            if kind == "order":
                to = str(it.get("to") or "?")
                nm = self._name_of(to) or to
                extra = ""
                if isinstance(it.get("x"), int) and \
                        isinstance(it.get("y"), int):
                    extra = " (%s,%s)" % (it["x"], it["y"])
                if it.get("quest"):   # #130: assign = quest accepted
                    return self._line(ts, "quest", "Quest Log", None,
                                      self._uid_of(to),
                                      "Quest accepted: %s -> %s%s" % (
                                          it["quest"], nm, extra))
                return self._line(ts, "order", "Cmdr", None,
                                  self._uid_of(to),
                                  "orders -> %s: %s%s" % (
                                      nm, it.get("order", "?"), extra))
            if kind == "spawn":
                return self._line(ts, "spawn", "Cmdr", None, None,
                                  "requisition: %s - %s" % (
                                      it.get("profile", "?"),
                                      str(it.get("task") or "")[:60]))
            if kind == "goal":
                return self._line(ts, "order", "Cmdr", None, None,
                                  "new main quest: %s" % str(
                                      it.get("text") or "")[:80])
            return None
        if et == "mail.deposit":
            m = ev.get("mail") or {}
            frm = self._name_of(m.get("from")) or str(
                m.get("from") or "?")
            to = self._name_of(m.get("to")) or str(m.get("to") or "?")
            return self._line(ts, "raven", "Raven", None,
                              self._uid_of(m.get("to")),
                              "%s -> %s: %s" % (frm, to, str(
                                  m.get("preview") or "")[:60]))
        if et == "agent.note":
            key = str(ev.get("agent") or "?")
            nm = self._name_of(key) or key
            return self._line(ts, "note", nm, None,
                              self._uid_of(key),
                              "reports: %s" % str(
                                  ev.get("note") or "")[:80])
        if et == "remote.open":
            return self._line(ts, "council", "Watchtower", None, None,
                              "remote link open on :%s (ttl %ss)" % (
                                  ev.get("port"), int(
                                      ev.get("ttl_s") or 0)))
        if et == "remote.expired":
            return self._line(ts, "council", "Watchtower", None, None,
                              "remote link closed")
        if et == "auth.deny":
            return self._line(ts, "council", "Watchtower", None, None,
                              "unauthorized contact turned away (%s)"
                              % ev.get("ip", "?"))
        return None

    def event_hint(self, ev):
        """Map-ping hint for a just-applied event: {kind, xy:[tx,ty]}.
        Called by rtsd after apply() so file_lanes reflect this event."""
        et = ev.get("type", "")
        if et == "mail.deposit":
            m = ev.get("mail") or {}
            th = self.sites.get("town-hall")
            home = list(th["xy"]) if th else [MAP_W // 2, MAP_H // 2]

            def endpoint(ref):
                uid = self._uid_of(ref)
                u = self.units.get(uid) if uid else None
                lane = (u or {}).get("lane")
                if lane in self.layout["capitals"]:
                    return list(self.layout["capitals"][lane])
                return home
            return {"kind": "raven", "from": endpoint(m.get("from")),
                    "to": endpoint(m.get("to"))}
        if et == "decision.created":
            s = self.sites.get("town-hall")
            return {"kind": "decision", "xy": s["xy"]} if s else None
        if et != "hook.posttooluse":
            return None
        tool = ev.get("tool") or ""
        ti = (ev.get("payload") or {}).get("tool_input") or {}
        if tool == "skill":                      # #132: ping the Library
            s = self.sites.get("library")
            return {"kind": "spell", "xy": s["xy"]} if s else None
        if tool in FILE_TOOLS:
            p = _input_path(ti)
            if not p:
                return None
            t = self.tile_of.get(p)
            if t is None:
                t = file_tile(self.layout, self.root, p)
            kind = ("contested"
                    if len(self.file_lanes.get(p, ())) > 1 else "file")
            return {"kind": kind, "xy": [t % MAP_W, t // MAP_W]}
        if tool in ("run_subagent", "read_subagent"):
            kind = "spawn"
            if tool == "read_subagent":
                resp = (ev.get("payload") or {}).get("tool_response")
                txt = resp if isinstance(resp, str) else json.dumps(
                    resp or "")
                if "fail" not in txt.lower() and "error" not in txt.lower():
                    return None
                kind = "fail"
            aid = str(ti.get("agent_id", ""))
            u = self.units.get(aid, {})
            lane = str(u.get("lane") or ti.get("lane") or "")
            reg = lane if lane in self.layout["capitals"] else "root"
            return {"kind": kind,
                    "xy": list(self.layout["capitals"][reg])}
        return None

    # issue #130: quest log. DONE/FAIL cover both the canonical local
    # triage labels and the "resolved" status the scratch issues actually
    # use. Dependency tokens may be short prefixes ("01" -> "01-x.md"),
    # GitHub refs ("#120" -> "120.md") or prose; only tokens that resolve
    # to a real issue id count toward blocking (raw text stays in
    # blocked_by for the dependency-chain display).
    _Q_DONE = {"done", "closed", "complete", "completed", "resolved"}
    _Q_FAIL = {"failed", "fail", "rework", "blocked-fail"}

    def _resolve_dep(self, dep, qs, effort):
        dep = dep.strip().lstrip("#")
        if not dep:
            return None
        pools = ([q["id"] for q in qs if q["effort"] == effort] +
                 [q["id"] for q in qs if q["effort"] != effort])
        for qid in pools:
            if qid == dep or qid.startswith(dep + "-") \
                    or qid.split("-")[0] == dep:
                return qid
        return None

    def _quests(self, by_lane=None):
        qs = scan_issues(self.root)
        done = {q["id"] for q in qs if q["status"] in self._Q_DONE}
        for q in qs:
            q["kind"] = "side"
            toks = [d.strip() for d in re.split(r"[,;\s]+",
                    q.get("blocked_by") or "")
                    if d.strip() and d.strip() != "-"]
            deps = []
            for t in toks:
                r = self._resolve_dep(t, qs, q["effort"])
                if r and r not in deps:
                    deps.append(r)
            q["deps"] = deps
            q["blocked"] = any(d not in done for d in deps)
            q["done"] = q["id"] in done
            q["failed"] = q["status"] in self._Q_FAIL
        # assignment: a hero's latest order carrying a quest ref marks it
        # as that quest's assignee (#130 assign flow); order lifecycle is
        # overlaid separately, so consumed quests stay on the hero's sheet
        latest = {}
        for uid, ords in self.orders.items():
            for o in reversed(ords):
                if o.get("quest"):
                    latest[uid] = str(o["quest"])
                    break
        # ledger link: a ledger named after the issue id wins (per-quest
        # gates), else the effort ledger (v1 convention)
        for q in qs:
            lid = None
            if by_lane:
                if q["id"] in by_lane:
                    lid = q["id"]
                elif q["effort"] in by_lane:
                    lid = q["effort"]
            q["ledger"] = lid
            if lid and by_lane:
                lg = by_lane[lid]
                q["gates"] = {"pass": lg["passed"],
                              "fail": sum(1 for g in lg["gates"]
                                          if g["state"] == "fail"),
                              "total": len(lg["gates"])}
            else:
                q["gates"] = None
            q["assignees"] = [u["id"] for u in self.units.values()
                              if latest.get(u["id"]) == q["id"]]
        if self.goal:
            qs.insert(0, {"id": "main-quest", "effort": "", "kind": "main",
                          "title": self.goal["text"], "status": "main",
                          "blocked_by": "", "deps": [], "blocked": False,
                          "done": False, "failed": False, "ledger": None,
                          "gates": None, "assignees": []})
        return qs

    def _breaches(self, by_lane, quests):
        """Failed ledger gates = wall breaches on their territory (#133).
        Region: a region literally named after the ledger, else the region
        holding a linked issue file's tile, else the keep ("root").
        Snapshot-derived from .devin/ledgers/*.md so replay stays pure;
        the territory glows until every gate in the ledger passes."""
        qreg = {}
        for q in quests:
            lid = q.get("ledger")
            if not lid or q["kind"] == "main" or lid in qreg:
                continue
            p = os.path.join(self.root, ".devin", "scratch", q["effort"],
                             "issues", q["id"] + ".md")
            t = file_tile(self.layout, self.root, p)
            qreg[lid] = self.layout["regions"][
                self.layout["tile_region"][t]]
        caps = self.layout["capitals"]
        out = []
        for lid, lg in sorted(by_lane.items()):
            if not lg["failed"]:
                continue
            reg = lid if lid in caps else qreg.get(lid, "root")
            out.append({"ledger": lid, "region": reg,
                        "xy": list(caps.get(reg)
                                   or [MAP_W // 2, MAP_H // 2]),
                        "gates": [g["id"] for g in lg["gates"]
                                  if g["state"] == "fail"]})
        return out

    def _quest_feed(self, qs, now):
        """Snapshot-time quest lines (#130): progress/completion is file
        state (issue Status + ledger gates), so these are computed, never
        appended to the event-sourced feed - replay stays pure."""
        lines = []
        for q in qs:
            if q["kind"] == "main":
                continue
            g = q.get("gates")
            if q["done"]:
                txt = ("Quest complete - reward: %s ledger GREEN (%d/%d)"
                       % (q["ledger"] or q["effort"], g["pass"],
                          g["total"]) if g else
                       "Quest complete: %s" % q["id"])
            elif g and g["fail"]:
                txt = ("Quest failed: %s - marker stays red until retried"
                       % q["id"])
            elif g and g["pass"]:
                txt = "Objective complete (%d/%d): %s" % (
                    g["pass"], g["total"], q["title"][:60])
            elif q["assignees"]:
                txt = "Quest accepted: %s" % q["id"]
            else:
                continue
            lines.append({"t": now, "kind": "quest", "who": "Quest Log",
                          "cls": None, "uid": (q["assignees"] or [None])[0],
                          "text": txt})
        return lines

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
        ist = self._intent_status()
        quests = self._quests(by_lane)
        qmap = {q["id"]: q for q in quests}
        for u in self.units.values():
            u = dict(u)
            if u["kind"] == "hero":
                u["status_live"] = self._live_status(u, now)
                # quest assignment (#130): the hero's latest order carrying
                # a quest ref binds it to that issue; HP/xp/loot then track
                # the issue's ledger gates (per-issue ledger wins, else the
                # effort ledger, else the lane ledger)
                qid = None
                for o in reversed(self.orders.get(u["id"], [])):
                    if o.get("quest"):
                        qid = str(o["quest"])
                        break
                if qid:
                    u["quest"] = qid
                lkey = (qmap[qid]["ledger"] if qid and qid in qmap
                        and qmap[qid].get("ledger") else None) \
                    or u.get("lane") or ""
                lane = by_lane.get(lkey)
                if lane:
                    total = len(lane["gates"]) or 1
                    u["hp"] = round(100 * lane["passed"] / total)
                    u["gate_fail"] = lane["failed"]
                    u["xp"] = u.get("xp", 0) + lane["passed"]
                    u["level"] = 1 + u["xp"] // 3
                    u["inventory"] = [
                        {"gate": g["id"],
                         "evidence": g.get("evidence", ""),
                         "ledger": lkey,
                         "quest": qid if lkey == (qmap.get(qid) or {})
                         .get("ledger") else None}
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
                # order queue (#127): lifecycle state overlaid from the
                # intent files (queued while pending, acknowledged once
                # the session consumed it, then 'consumed'/cleared)
                u["orders"] = [self._order_view(
                    i, ist.get(str(i.get("id")), "pending"))
                    for i in self.orders.get(u["id"], [])]
                # #131 economy: this hero's context burn = est tokens on
                # its lane; turns_left = remaining window (mana % of the
                # model context window) / avg burn per tool call there
                ln = u.get("lane") or ""
                ub = self.burn.get(ln, 0)
                u["burn"] = ub
                if u.get("mana") is not None and ub and self._window:
                    avg = ub / max(1, self.burn_calls.get(ln, 1))
                    u["turns_left"] = int(
                        (u["mana"] / 100.0 * self._window) / max(1, avg))
                else:
                    u["turns_left"] = None
                # #132 spellbook: skills the profile sheet names as its
                # own kit; innate abilities are u["kit"] (allowed-tools)
                u["spellbook"] = [{"name": n,
                                   "casts": (self.skill_casts.get(n) or {})
                                   .get("n", 0)}
                                  for n in profile_skills(
                                      self.root, u.get("profile") or "")]
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
        supply_minions = sum(1 for u in self.units.values()
                             if u["kind"] == "minion")
        # income rate (#131): est tokens from PostToolUse events inside
        # the trailing 60s window; last5 feeds the HUD trend bars
        income_min = sum(g["amt"] for g in self.gold_log
                         if now - g["ts"] <= 60)
        income_last5 = [g["amt"] for g in self.gold_log[-5:]]
        workers = [wk for wk in self.workers
                   if now - wk["ts"] <= WORKER_WINDOW_S]
        wunits = [{"id": "wk-%d" % i, "kind": "worker", "tool": wk["tool"],
                   "ts": wk["ts"], "from": wk["from"], "to": wk["to"]}
                  for i, wk in enumerate(workers[-8:])]
        regions = self._region_list()
        fog, mark, pois = self._fog_mark(now, by_lane)
        # idle-worker button (#127): heroes with no active order; fleet
        # status cross-checked via status_live (idle/stale, not busy)
        idle = [u["id"] for u in units
                if u.get("kind") == "hero"
                and u.get("status_live") in ("idle", "stale")
                and not any(o.get("state") != "consumed"
                            for o in u.get("orders", []))]
        return {
            "now": now,
            "units": units,
            "idle": idle,
            # comms scrollback (#128) + quest log lines (#130): the quest
            # lines are snapshot-derived (issue status + ledger gates),
            # appended after the event feed so replay stays pure
            "feed": self.feed[-80:] + self._quest_feed(quests, now),
            "mail": self.mail[-20:],       # recent mailbox deposits
            "workers": wunits,
            "buildings": [dict(b, pos=self.sites.get(b["id"]),
                             rally=self.rally_of(b["id"]))
                          for b in self.buildings.values()],
            "resources": {"gold": gold, "lumber_pct": lumber_pct,
                          "supply_used": supply_used,
                          "supply_heroes": supply_used,
                          "supply_minions": supply_minions,
                          "supply_cap": SUPPLY_CAP, "upkeep": upkeep,
                          "income_min": income_min,
                          "income_last5": income_last5,
                          "thresholds": {"warn": w, "crit": c,
                                         "clear": clr},
                          "window": self._window},
            "quests": quests,
            # #133 breach alarms: ledgers with failed gates keep their
            # territory glowing red until the gate set is green again
            "breaches": self._breaches(by_lane, quests),
            # #132 tech tree: real skills grouped by school with cast
            # state, armory model tiers, memory doctrines - all derived
            # from files + the event-sourced skill_casts ledger
            "tech": {"schools": tech_tree(self.root, self.skill_casts),
                     "armory": armory(self.root),
                     "doctrines": doctrines(self.root)},
            "map": {"root": self.root, "sig": self.layout["sig"],
                    "w": MAP_W, "h": MAP_H,
                    "tile_region": self.layout["tile_region"],
                    "fog": fog, "mark": mark, "pois": pois,
                    "regions": regions,
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
