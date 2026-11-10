#!/usr/bin/env python3
"""pulse - drain due .devin/rts/intents/*.json into one afk-loop frontier step.

Near-loop trigger (liquid-software pattern): rl-resume-detect.py writes
intent files {"kind": "resume_at", "when": <epoch>, "auto": bool, ...}.
This script is the executor the intents never had:

- scans intents; finds those due (when <= now);
- REFUSES intents with auto:false (opt-out respected, never executed);
- for due auto-executing intents, computes the afk-loop frontier over
  .devin/scratch/*/issues/*.md and emits the next ready issue key;
- consumed intents get marked (consumed:true) so they drain once.

Usage: pulse.py [--dry-run] [--intents-dir DIR] [--issues-glob GLOB]
JSON to stdout. Exit 0 ok, 2 on misuse.
"""
import glob
import json
import os
import re
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STATUS_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Status(?:\*\*)?\s*:\s*(\w+)",
                       re.I | re.M)
BLOCKED_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?Blocked by(?:\*\*)?\s*:\s*(.+)$", re.I | re.M)
KEY_RE = re.compile(r"([#\w-]*\d[\w-]*)")


def load_intents(d):
    out = []
    for path in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            data = json.loads(open(path, encoding="utf-8",
                                   errors="replace").read())
            out.append({"path": path, **data})
        except (OSError, ValueError):
            out.append({"path": path, "kind": "invalid", "auto": False})
    return out


def issue_status(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None, []
    m = STATUS_RE.search(text)
    status = (m.group(1).lower() if m else "open")
    b = BLOCKED_RE.search(text)
    blockers = KEY_RE.findall(b.group(1)) if b else []
    return status, blockers


def frontier(issues_glob):
    tickets = {}
    for path in sorted(glob.glob(issues_glob, recursive=True)):
        key = os.path.splitext(os.path.basename(path))[0]
        status, blockers = issue_status(path)
        if status is None:
            continue
        tickets[key] = {"status": status, "blockers": blockers,
                        "path": path}
    resolved = {k for k, t in tickets.items() if t["status"] == "resolved"}
    ready = [k for k, t in tickets.items()
             if t["status"] not in ("resolved", "claimed")
             and all(b in resolved or b not in tickets for b in t["blockers"])]
    def num(k):
        m = re.search(r"\d+", k)
        return int(m.group(0)) if m else 10 ** 9
    ready.sort(key=num)
    return ready[0] if ready else None, tickets


def main(argv):
    dry = "--dry-run" in argv
    intents_dir = ".devin/rts/intents"
    issues_glob = ".devin/scratch/*/issues/*.md"
    for i, a in enumerate(argv):
        if a == "--intents-dir" and i + 1 < len(argv):
            intents_dir = argv[i + 1]
        if a == "--issues-glob" and i + 1 < len(argv):
            issues_glob = argv[i + 1]
    now = int(time.time())
    due, refused, pending = [], [], []
    for it in load_intents(intents_dir):
        if it.get("kind") != "resume_at":
            continue
        if it.get("consumed"):
            continue
        if int(it.get("when", 0)) > now:
            pending.append(it["path"])
            continue
        if it.get("auto") is False:
            refused.append({"path": it["path"],
                            "reason": "auto:false - opt-out respected"})
            continue
        due.append(it)
    next_issue, tickets = frontier(issues_glob)
    if due and not dry:
        for it in due:
            it["consumed"] = True
            it["consumed_at"] = now
            with open(it["path"], "w", encoding="utf-8") as f:
                json.dump({k: v for k, v in it.items() if k != "path"}, f)
    print(json.dumps({
        "ok": True, "dry_run": dry, "now": now,
        "due": [os.path.basename(x["path"]) for x in due],
        "refused": refused, "pending": [os.path.basename(p) for p in pending],
        "frontier_total": len(tickets),
        "next_issue": next_issue,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
