#!/usr/bin/env python3
"""roadmap-board - macro-layer roadmap over local Markdown issues.

Scans .devin/issues/*.md and .devin/scratch/*/issues/*.md, extracts
title/status/priority/blocked-by/blocks metadata, and renders a
Markdown board: per-effort sections, frontier (unblocked non-resolved
items), and burndown counts. Composes the micro/meso layers into the
macro view tracked by issue #346.

Stdlib only, read-only, deterministic. Exit 0 always; --json emits the
parsed model instead of Markdown.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import status_vocab  # noqa: E402

# tolerant field prefix: '- ', '**', '`' around name AND colon in any
# order - covers 'Status: x', '- **Status**: x', '**Status:** x'
_FIELD = (r"^\s*(?:[-*]\s*)?\*{{0,2}}{}\*{{0,2}}:?\*{{0,2}}"
          r"\s*[:=]?\s*")
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)
STATUS_RE = re.compile(r"(?im)" + _FIELD.format("status") + r"([\w-]+)")
PRIORITY_RE = re.compile(r"(?im)" + _FIELD.format("priority") + r"([\w-]+)")
ESTIMATE_RE = re.compile(
    r"(?im)" + _FIELD.format("estimate[_-]?min") + r"(\d+)")
ACTUAL_RE = re.compile(
    r"(?im)" + _FIELD.format("actual[_-]?min") + r"(\d+)")
# blocked-by/blocks appear inline in milestone meta lines
# ("Status: x · Blocked-by: y") AND as markdown field lines - keep
# unanchored; _split_ids strips any '**' residue from captures.
BLOCKED_BY_RE = re.compile(r"(?i)blocked[-_ ]by\s*[:=]\s*([^\n·|]+)")
BLOCKS_RE = re.compile(r"(?i)(?<![-\w])blocks\s*[:=]\s*([^\n·|]+)")
_MD_CHARS = re.compile(r"[*`\[\]()]")  # not '_': keys use it (MILESTONE_2_01)
_PREFIX_REF = re.compile(r"[0-9A-Za-z]+")


# effort-level archive marker (issue #406): scratch/<effort>/README.md
# 'Status: ARCHIVED' field - detection lives in status_vocab so the
# site issue ledger applies the same exclusion (#407 unification)
archived_efforts = status_vocab.archived_efforts


def _count_issue_files(root, effort):
    idir = os.path.join(root, ".devin", "scratch", effort, "issues")
    try:
        return sum(1 for f in os.listdir(idir) if f.endswith(".md"))
    except OSError:
        return 0


def _iter_issue_files(root):
    issues_dir = os.path.join(root, ".devin", "issues")
    if os.path.isdir(issues_dir):
        for f in sorted(os.listdir(issues_dir)):
            if f.endswith(".md"):
                yield os.path.join(issues_dir, f), "issues"
    scratch = os.path.join(root, ".devin", "scratch")
    if os.path.isdir(scratch):
        for effort in sorted(os.listdir(scratch)):
            idir = os.path.join(scratch, effort, "issues")
            if os.path.isdir(idir):
                for f in sorted(os.listdir(idir)):
                    if f.endswith(".md"):
                        yield os.path.join(idir, f), effort


def _first(pat, text):
    m = pat.search(text)
    return m.group(1).strip() if m else None


def _split_ids(raw):
    if not raw:
        return []
    raw = raw.strip().strip("`.").rstrip(".")
    out = []
    for t in re.split(r"[,;]|\band\b", raw):
        # strip markdown emphasis/links residue (**Blocked by:** lines
        # capture the closing ** - issue #402)
        t = _MD_CHARS.sub("", t).strip().strip("`.").rstrip(".")
        if not t or t.lower() in ("none", "n/a", "-", ""):
            continue
        # prose tails like "None - can start immediately" -> none;
        # append the stripped head, not the raw token (review: tails
        # like "M2-01 - pending" never resolved -> inflated unknowns)
        head = re.split(r"\s+[—–-]\s+|\s{2,}", t)[0].strip()
        if head.lower() in ("none", "n/a", "-"):
            continue
        out.append(head)
    return out


def parse_issue(path, group):
    text = open(path, encoding="utf-8", errors="replace").read()
    title = _first(TITLE_RE, text) or os.path.splitext(
        os.path.basename(path))[0]
    status = (_first(STATUS_RE, text) or "open").lower()
    blocked_by = _split_ids(_first(BLOCKED_BY_RE, text))
    # milestone files carry "Blocked-by:" inline in the meta line;
    # scratch issues may carry a markdown "blocked_by:" field too
    if not blocked_by:
        m = re.search(r"(?im)^\s*blocked[_-]by\s*[:=]\s*(.+)$", text)
        blocked_by = _split_ids(m.group(1)) if m else []
    blocks = _split_ids(_first(BLOCKS_RE, text))
    est = _first(ESTIMATE_RE, text)
    act = _first(ACTUAL_RE, text)
    stem = os.path.splitext(os.path.basename(path))[0]
    return {
        "key": stem, "title": title, "group": group, "path": path,
        "status": status, "done": status_vocab.is_terminal(status),
        "priority": (_first(PRIORITY_RE, text) or "").upper() or None,
        "estimate_min": int(est) if est else None,
        "actual_min": int(act) if act else None,
        "blocked_by": blocked_by, "blocks": blocks,
    }


def _aliases(issue):
    """Names other issues may use to reference this one."""
    k = issue["key"]
    out = {k.lower()}
    m = re.match(r"MILESTONE_2_(\d+)", k, re.I)
    if m:
        out.add(f"m2_{int(m.group(1)):02d}")
        out.add(f"m2_{m.group(1)}")
    m = re.match(r"ISSUE_(\d+)", k, re.I)
    if m:
        out.add(f"issue_{m.group(1)}")
        out.add(f"issue {m.group(1)}")
    return out


def _group_prefix_match(ref, group, issues):
    """Same-effort numeric-prefix resolution (issue #403): scratch DAGs
    reference siblings as '01', '02' etc. Only matches within the same
    group - many efforts have their own 01-*.md."""
    ref_l = ref.strip().lower()
    if (not ref_l or not ref_l[0].isdigit()
            or not _PREFIX_REF.fullmatch(ref_l) or len(ref_l) > 12):
        return None
    for cand in issues:
        if cand["group"] != group:
            continue
        k = cand["key"].lower()
        first = k.split("-", 1)[0]
        if k == ref_l or first == ref_l or k.startswith(ref_l + "-"):
            return cand
    return None


def build_model(root):
    archived = set(status_vocab.archived_efforts(root))
    issues = [parse_issue(p, g) for p, g in _iter_issue_files(root)
              if g not in archived]
    by_alias = {}
    for i in issues:
        for a in _aliases(i):
            by_alias[a] = i
    for i in issues:
        resolved = []
        for b in i["blocked_by"]:
            ref = b.lower().strip()
            hit = by_alias.get(ref)
            via = "alias" if hit else None
            if hit is None:
                hit = _group_prefix_match(ref, i["group"], issues)
                via = "group-prefix" if hit else None
            resolved.append({
                "ref": b,
                "known": hit is not None,
                "done": bool(hit and hit["done"]),
                "via": via,
            })
        i["blockers"] = resolved
        i["ready"] = (not i["done"]
                      and status_vocab.is_claimable(i["status"])
                      and all(b["done"] or not b["known"]
                              for b in resolved))
    return issues


def summarize(issues):
    done = sum(1 for i in issues if i["done"])
    return {"total": len(issues), "done": done,
            "open": len(issues) - done,
            "ready": sum(1 for i in issues if i["ready"]),
            "blocked_unknown": sum(
                1 for i in issues if not i["done"] and any(
                    not b["known"] for b in i["blockers"]))}


def _goal_field(text, name):
    m = re.search(r"(?im)" + _FIELD.format(name) + r"([^\n]+)", text)
    return m.group(1).strip() if m else None


def _goal_list(text, name):
    val = _goal_field(text, name)
    return [t for t in re.split(r"[,\s]+", val) if t] if val else []


def load_goals(root, issues):
    """Macro goal rollup (issue #420): read .devin/goals/*.md.

    Goal files declare Status/Horizon/Objective plus link sets:
    Efforts: <group,...> scores every issue in those groups, Issues:
    <key,...> scores explicit keys (group/key accepted), Refs: <tokens>
    is traceability only (e.g. GitHub '#417') and never scored.
    Coverage = done/linked over resolvable local issues.
    """
    gdir = os.path.join(root, ".devin", "goals")
    if not os.path.isdir(gdir):
        return []
    by_key = {}
    for i in issues:
        by_key.setdefault(i["key"], []).append(i)
        by_key.setdefault(i["group"] + "/" + i["key"], []).append(i)
    goals = []
    for fn in sorted(os.listdir(gdir)):
        if not fn.endswith(".md") or fn == "README.md":
            continue
        path = os.path.join(gdir, fn)
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        title = TITLE_RE.search(text)
        efforts = _goal_list(text, "efforts")
        ikeys = _goal_list(text, "issues")
        refs = _goal_list(text, "refs")
        linked, unresolved, seen = [], [], set()
        for e in efforts:
            for i in issues:
                if i["group"] == e and (i["group"], i["key"]) not in seen:
                    seen.add((i["group"], i["key"]))
                    linked.append(i)
        for k in ikeys:
            hit = by_key.get(k)
            if hit:
                for i in hit:
                    if (i["group"], i["key"]) not in seen:
                        seen.add((i["group"], i["key"]))
                        linked.append(i)
            else:
                unresolved.append(k)
        raw_title = title.group(1).strip() if title else fn
        raw_title = re.sub(r"^goal\s*:\s*", "", raw_title, flags=re.I)
        done = sum(1 for i in linked if i["done"])
        goals.append({
            "name": os.path.splitext(fn)[0],
            "title": raw_title or fn,
            "status": (_goal_field(text, "status") or "active").lower(),
            "horizon": _goal_field(text, "horizon"),
            "objective": _goal_field(text, "objective"),
            "efforts": efforts, "refs": refs,
            "linked": len(linked), "done": done,
            "coverage": (round(done / len(linked), 3)
                         if linked else None),
            "unresolved": unresolved})
    return goals


def _cap_bucket():
    return {"total": 0, "done": 0, "open": 0, "ready": 0,
            "blocked": 0, "in_flight": 0, "est_open_min": 0}


def capacity(issues, wip_limit=None):
    """Meso capacity/WIP view (issue #417): per-effort load vs frontier.

    open = not done; ready = claimable now (status claimable + blockers
    satisfied); blocked = open and not ready (includes blocked status,
    undone blockers, non-actionable and in-flight work); in_flight =
    status in status_vocab.IN_FLIGHT (subset marker, may overlap
    blocked). Status vocabulary is shared with site/build.py (#407).
    """
    groups = {}
    for i in issues:
        g = groups.setdefault(i["group"], _cap_bucket())
        g["total"] += 1
        if i["done"]:
            g["done"] += 1
            continue
        g["open"] += 1
        if i.get("estimate_min"):
            g["est_open_min"] += i["estimate_min"]
        if i["ready"]:
            g["ready"] += 1
        else:
            g["blocked"] += 1
        if i["status"] in status_vocab.IN_FLIGHT:
            g["in_flight"] += 1
    totals = _cap_bucket()
    for g in groups.values():
        for k in totals:
            totals[k] += g[k]
    return {"by_group": groups, "totals": totals,
            "frontier": totals["ready"],
            "wip": {"in_flight": totals["in_flight"],
                    "limit": wip_limit,
                    "over": (totals["in_flight"] > wip_limit
                             if wip_limit is not None else None)}}


def pending_decisions(root):
    """Unresolved human-blocking stops recorded by decision-queue.py."""
    path = os.path.join(root, ".devin", "decisions.jsonl")
    n = 0
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            if line.strip():
                try:
                    if not json.loads(line).get("resolved"):
                        n += 1
                except ValueError:
                    continue
    except OSError:
        pass
    return n


def render_md(issues, root):
    s = summarize(issues)
    archived = status_vocab.archived_efforts(root)
    arch_n = sum(_count_issue_files(root, e) for e in archived)
    lines = [
        "# Roadmap board (generated by scripts/roadmap-board.py)",
        "",
        f"- Issues: {s['total']} total, {s['done']} done, "
        f"{s['open']} open, {s['ready']} frontier-ready, "
        f"{s['blocked_unknown']} with unresolved blocker refs",
    ]
    pd = pending_decisions(root)
    if pd:
        lines.append(f"- Pending decisions (human-blocking): {pd} "
                     "(.devin/decisions.jsonl)")
    lines.append("")
    if archived:
        lines.append(
            f"- Archived efforts excluded: {arch_n} issues across "
            f"{len(archived)} efforts ({', '.join(archived)})")
        lines.append("")
    groups = {}
    for i in issues:
        groups.setdefault(i["group"], []).append(i)
    for g in sorted(groups):
        items = groups[g]
        gd = sum(1 for i in items if i["done"])
        lines.append(f"## {g} ({gd}/{len(items)} done)")
        lines.append("")
        for i in sorted(items, key=lambda x: (x["done"], x["key"])):
            mark = "x" if i["done"] else ("ready" if i["ready"] else "open")
            pri = f" [{i['priority']}]" if i["priority"] else ""
            lines.append(f"- [{mark}] {i['title']}{pri}")
        lines.append("")
    ready = [i for i in issues if i["ready"]]
    if ready:
        lines.append("## Frontier (claimable now)")
        lines.append("")
        for i in sorted(ready, key=lambda x: x["key"]):
            lines.append(f"- {i['title']} ({i['group']}/{i['key']})")
        lines.append("")
    cap = capacity(issues)
    lines.append("## Capacity")
    lines.append("")
    lines.append("| Group | Open | Ready | Not ready | In-flight | Est min |")
    lines.append("|---|---|---|---|---|---|")
    for g in sorted(cap["by_group"]):
        b = cap["by_group"][g]
        lines.append(f"| {g} | {b['open']} | {b['ready']} | "
                     f"{b['blocked']} | {b['in_flight']} | "
                     f"{b['est_open_min'] or '-'} |")
    t = cap["totals"]
    lines.append(f"| **total** | {t['open']} | {t['ready']} | "
                 f"{t['blocked']} | {t['in_flight']} | "
                 f"{t['est_open_min'] or '-'} |")
    lines.append("")
    lines.append(f"Frontier: {cap['frontier']} claimable - "
                 f"WIP in-flight: {cap['wip']['in_flight']}")
    lines.append("")
    goals = load_goals(root, issues)
    if goals:
        lines.append("## Goals")
        lines.append("")
        lines.append("| Goal | Status | Horizon | Coverage |")
        lines.append("|---|---|---|---|")
        for g in goals:
            cov = (f"{g['done']}/{g['linked']}"
                   if g["linked"] else "-")
            lines.append(f"| {g['title']} | {g['status']} | "
                         f"{g['horizon'] or '-'} | {cov} |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None,
                    help="repo root (default: DEVIN_PROJECT_DIR or cwd)")
    ap.add_argument("--json", action="store_true", help="emit JSON model")
    ap.add_argument("--wip-limit", type=int, default=None,
                    help="in-flight WIP ceiling; capacity.wip.over flags "
                         "when in_flight exceeds it")
    args = ap.parse_args(argv)
    root = args.root or os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    issues = build_model(root)
    archived = status_vocab.archived_efforts(root)
    if args.json:
        print(json.dumps({"summary": {**summarize(issues),
                                      "archived_efforts": archived,
                                      "archived_issues": sum(
                                          _count_issue_files(root, e)
                                          for e in archived)},
                          "capacity": capacity(issues, args.wip_limit),
                          "pending_decisions": pending_decisions(root),
                          "goals": load_goals(root, issues),
                          "issues": issues}, ensure_ascii=False, indent=1))
    else:
        print(render_md(issues, root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
