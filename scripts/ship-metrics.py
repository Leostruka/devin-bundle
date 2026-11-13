#!/usr/bin/env python3
"""ship-metrics — DORA-style lead-time log for the ship loop (#486).

Every merged PR appends one JSON line to .devin/metrics/ships.jsonl.
Without measured lead time, "the loop got faster" is a guess — the
same Rule-15 standard applied to product metrics applies to the
process itself.

  ship-metrics.py backfill [--limit 50]   pull merged PRs from gh
  ship-metrics.py record --pr N           append one PR
  ship-metrics.py report                  lead-time stats over the log

Stdlib + gh CLI. Idempotent: existing PR numbers are skipped.
"""
import argparse
import json
import os
import subprocess
import sys

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from bundle_envelope import bind


_stamp, _dumps = bind("ship-metrics")


FIELDS = ("number,title,createdAt,mergedAt,additions,deletions,"
          "changedFiles,author")


def _gh_prs(limit):
    cmd = ["gh", "pr", "list", "--state", "merged", "--limit",
           str(limit), "--json", FIELDS]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    if p.returncode != 0:
        sys.exit(f"gh pr list failed: {p.stderr.strip()[:200]}")
    return json.loads(p.stdout or "[]")


def _gh_pr(n):
    cmd = ["gh", "pr", "view", str(n), "--json", FIELDS]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=30)
    if p.returncode != 0:
        sys.exit(f"gh pr view {n} failed: {p.stderr.strip()[:200]}")
    return json.loads(p.stdout or "{}")


def _load(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _row(pr):
    from datetime import datetime
    ca = datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
    ma = datetime.fromisoformat(
        (pr.get("mergedAt") or pr["createdAt"]).replace("Z", "+00:00"))
    return {
        "pr": pr["number"],
        "title": pr.get("title", "")[:120],
        "author": (pr.get("author") or {}).get("login", ""),
        "created_at": pr["createdAt"],
        "merged_at": pr.get("mergedAt"),
        "lead_min": round((ma - ca).total_seconds() / 60, 1),
        "files": pr.get("changedFiles", 0),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
    }


def _merge_rows(path, prs):
    have = {r["pr"] for r in _load(path)}
    new = [_row(p) for p in prs if p["number"] not in have]
    if not new:
        return 0
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(new)


def report(path):
    rows = [r for r in _load(path) if r.get("lead_min") is not None]
    if not rows:
        print(_dumps({"ok": True, "n": 0}))
        return
    leads = sorted(r["lead_min"] for r in rows)
    n = len(leads)
    med = leads[n // 2] if n % 2 else (leads[n // 2 - 1]
                                     + leads[n // 2]) / 2
    print(_dumps({
        "ok": True, "n": n,
        "lead_min": {"median": med, "p90": leads[int(n * .9)],
                     "max": leads[-1]},
        "files_median": sorted(r["files"] for r in rows)[n // 2],
        "additions_total": sum(r["additions"] for r in rows),
    }, indent=2))


def main():
    ap = argparse.ArgumentParser(prog="ship-metrics")
    ap.add_argument("--log",
                    default=".devin/metrics/ships.jsonl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backfill")
    b.add_argument("--limit", type=int, default=50)
    r = sub.add_parser("record")
    r.add_argument("--pr", type=int, required=True)
    sub.add_parser("report")
    a = ap.parse_args()
    if a.cmd == "backfill":
        n = _merge_rows(a.log, _gh_prs(a.limit))
    elif a.cmd == "record":
        n = _merge_rows(a.log, [_gh_pr(a.pr)])
    else:
        report(a.log)
        return
    print(_dumps({"ok": True, "appended": n, "log": a.log}))


if __name__ == "__main__":
    main()
