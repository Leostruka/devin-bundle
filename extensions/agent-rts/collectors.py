"""collectors - repository telemetry for agent-rts (GDD section 7).

Each collector is a small function returning a JSON-safe dict. All are
fail-open: a missing tool or repo surface yields an empty/partial section,
never an exception. Results are TTL-cached so the 2s tick stays cheap.

Sections: git (branch/dirty/worktrees), issues (gh + scratch), forge
(prompt_compiler output state), ledgers (open gates), gas (context
headroom), supply (concurrency + load).
"""
import json
import os
import re
import shutil
import subprocess
import time

_CACHE = {}
TTL = {"git": 5.0, "issues": 30.0, "forge": 5.0, "ledgers": 10.0,
       "gas": 10.0, "supply": 2.0}
SUPPLY_CAP = 8  # mirrors world.py (design cap on concurrent heroes)


def bust():
    _CACHE.clear()


def _cached(key, fn):
    ent = _CACHE.get(key)
    if ent and time.time() - ent[0] < TTL.get(key, 5.0):
        return ent[1]
    val = fn()
    _CACHE[key] = (time.time(), val)
    return val


def _run(root, args, timeout=5.0):
    try:
        # gh/git emit UTF-8; the Windows default codec (cp1252) would
        # mojibake accents in issue titles and dirty paths
        p = subprocess.run(args, cwd=root, capture_output=True,
                           text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return p.stdout if p.returncode == 0 else None
    except Exception:
        return None


def git_state(root):
    def go():
        out = {"available": shutil.which("git") is not None}
        if not out["available"]:
            return out
        br = _run(root, ["git", "branch", "--show-current"])
        out["branch"] = (br or "").strip() or None
        st = _run(root, ["git", "status", "--porcelain"])
        out["dirty"] = [ln[3:].strip() for ln in (st or "").splitlines()
                        if ln.strip()]
        wt = _run(root, ["git", "worktree", "list", "--porcelain"])
        trees, cur = [], {}
        for ln in (wt or "").splitlines():
            if ln.startswith("worktree "):
                cur = {"path": ln[9:].strip()}
                trees.append(cur)
            elif ln.startswith("branch "):
                cur["branch"] = ln[7:].strip().replace("refs/heads/", "")
        out["worktrees"] = trees
        return out
    return _cached("git", go)


def gh_issues(root):
    def go():
        out = {"available": shutil.which("gh") is not None, "open": []}
        if not out["available"]:
            return out
        raw = _run(root, ["gh", "issue", "list", "--state", "open",
                          "--json", "number,title,labels,createdAt",
                          "--limit", "25"], timeout=15.0)
        try:
            items = json.loads(raw or "[]")
        except Exception:
            items = []
        now = time.time()
        for it in items:
            try:
                age = now - time.mktime(time.strptime(
                    it.get("createdAt", "")[:19], "%Y-%m-%dT%H:%M:%S"))
            except Exception:
                age = 0
            out["open"].append({
                "n": it.get("number"), "title": it.get("title"),
                "age_s": int(max(0, age)),
                "labels": [l.get("name") for l in it.get("labels", [])
                           if isinstance(l, dict)]})
        return out
    return _cached("issues", go)


def scratch_issues(root):
    """Local .devin/scratch/**/issues/*.md treated as tickets too."""
    out = []
    sdir = os.path.join(root, ".devin", "scratch")
    for dp, _dn, fns in os.walk(sdir):
        if os.path.basename(dp) != "issues":
            continue
        for fn in fns:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dp, fn)
            try:
                st = os.stat(p)
                with open(p, encoding="utf-8") as f:
                    title = f.readline().lstrip("# ").strip()
                out.append({"n": fn[:-3], "title": title or fn,
                            "age_s": int(max(0, time.time() - st.st_mtime)),
                            "labels": ["local"],
                            "src": os.path.relpath(p, root)})
            except OSError:
                pass
    return out[:25]


def forge_state(root):
    def go():
        p = os.path.join(root, ".devin", "scratch", "optimized_ready.md")
        ok = os.path.isfile(p)
        return {"optimized_ready": ok,
                "mtime": os.stat(p).st_mtime if ok else None}
    return _cached("forge", go)


def ledgers_state(root):
    def go():
        ldir = os.path.join(root, ".devin", "ledgers")
        out = []
        if os.path.isdir(ldir):
            for fn in sorted(os.listdir(ldir)):
                if not fn.endswith(".md"):
                    continue
                try:
                    with open(os.path.join(ldir, fn),
                              encoding="utf-8") as f:
                        txt = f.read()
                    out.append({"name": fn,
                                "open_gates": len(re.findall(
                                    r"- \[ \]", txt)),
                                "done_gates": len(re.findall(
                                    r"- \[x\]", txt, re.I))})
                except OSError:
                    pass
        return out
    return _cached("ledgers", go)


def context_windows(root):
    try:
        with open(os.path.join(root, "data", "bundle-models.json"),
                  encoding="utf-8") as f:
            models = json.load(f).get("models", [])
        return {m["id"]: m.get("context_window", 262144)
                for m in models if isinstance(m, dict) and m.get("id")}
    except Exception:
        return {"swe-2-max": 262144}


def gas_state(root, world):
    """Vespene: free context-window headroom. Usage estimate comes from
    world.burn (event-sourced chars/4 per lane); the window comes from
    bundle-models.json. Under ~10% free the HUD fires context_low."""
    def go():
        wins = context_windows(root)
        model = getattr(world, "_submodel", "swe-2-max")
        window = wins.get(model, 262144)
        used = int(sum(getattr(world, "burn", {}).values()))
        free_pct = max(0.0, 100.0 * (1.0 - used / float(window or 1)))
        return {"model": model, "context_window": window,
                "used_est": used, "free_pct": round(free_pct, 1)}
    return _cached("gas", go)


def supply_state(root, world):
    def go():
        used = len(getattr(world, "units", {}) or {})
        load = None
        try:
            load = os.getloadavg()[0]  # absent on Windows -> None
        except (OSError, AttributeError):
            pass
        return {"used": used, "cap": SUPPLY_CAP,
                "workers": len(getattr(world, "workers", []) or []),
                "load1": load}
    return _cached("supply", go)


def pending_decisions(root):
    ddir = os.path.join(root, ".devin", "rts", "decisions")
    out = []
    if os.path.isdir(ddir):
        for fn in sorted(os.listdir(ddir)):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(ddir, fn), encoding="utf-8") as f:
                    d = json.load(f)
            except Exception:
                continue
            if d.get("status") == "pending":
                out.append(d)
    return out


def recent_intents(root, limit=30):
    idir = os.path.join(root, ".devin", "rts", "intents")
    out = []
    if os.path.isdir(idir):
        for fn in sorted(os.listdir(idir))[-limit:]:
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(idir, fn), encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                pass
    return out


def telemetry(root, world):
    """The snapshot's repo.* block: every collector, each fail-open."""
    gh = gh_issues(root)
    return {
        "git": git_state(root),
        "issues": (gh.get("open") or []) + scratch_issues(root),
        "issues_available": gh.get("available", False),
        "forge": forge_state(root),
        "ledgers": ledgers_state(root),
        "gas": gas_state(root, world),
        "supply": supply_state(root, world),
    }
