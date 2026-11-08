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

TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)
STATUS_RE = re.compile(r"(?im)^\s*(?:status|Status)\s*[:=]\s*([\w-]+)")
PRIORITY_RE = re.compile(r"(?im)^\s*priority\s*[:=]\s*([\w-]+)")
BLOCKED_BY_RE = re.compile(r"(?i)blocked[-_ ]by\s*[:=]\s*([^\n·|]+)")
BLOCKS_RE = re.compile(r"(?i)(?<![-\w])blocks\s*[:=]\s*([^\n·|]+)")
_MD_CHARS = re.compile(r"[*`\[\]()]")  # not '_': keys use it (MILESTONE_2_01)
_PREFIX_REF = re.compile(r"[0-9A-Za-z]+")


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
        # prose tails like "None - can start immediately" -> none
        head = re.split(r"\s+[—–-]\s+|\s{2,}", t)[0].strip()
        if head.lower() in ("none", "n/a", "-"):
            continue
        out.append(t)
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
    stem = os.path.splitext(os.path.basename(path))[0]
    return {
        "key": stem, "title": title, "group": group, "path": path,
        "status": status, "done": status_vocab.is_terminal(status),
        "priority": (_first(PRIORITY_RE, text) or "").upper() or None,
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
    issues = [parse_issue(p, g) for p, g in _iter_issue_files(root)]
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


def _cap_bucket():
    return {"total": 0, "done": 0, "open": 0, "ready": 0,
            "blocked": 0, "in_flight": 0}


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


def render_md(issues, root):
    s = summarize(issues)
    lines = [
        "# Roadmap board (generated by scripts/roadmap-board.py)",
        "",
        f"- Issues: {s['total']} total, {s['done']} done, "
        f"{s['open']} open, {s['ready']} frontier-ready, "
        f"{s['blocked_unknown']} with unresolved blocker refs",
        "",
    ]
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
    lines.append("| Group | Open | Ready | Not ready | In-flight |")
    lines.append("|---|---|---|---|---|")
    for g in sorted(cap["by_group"]):
        b = cap["by_group"][g]
        lines.append(f"| {g} | {b['open']} | {b['ready']} | "
                     f"{b['blocked']} | {b['in_flight']} |")
    t = cap["totals"]
    lines.append(f"| **total** | {t['open']} | {t['ready']} | "
                 f"{t['blocked']} | {t['in_flight']} |")
    lines.append("")
    lines.append(f"Frontier: {cap['frontier']} claimable - "
                 f"WIP in-flight: {cap['wip']['in_flight']}")
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
    if args.json:
        print(json.dumps({"summary": summarize(issues),
                          "capacity": capacity(issues, args.wip_limit),
                          "issues": issues}, ensure_ascii=False, indent=1))
    else:
        print(render_md(issues, root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
