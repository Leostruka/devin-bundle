#!/usr/bin/env python3
"""Shared issue-status vocabulary (issues #405, #407).

Single source of truth consumed by scripts/roadmap-board.py and
site/build.py so both surfaces agree on done-ness. Reconciles the
observed corpus statuses with .devin/agents/triage-labels.md.

Layers:
  DONE       - work completed (counts as finished in burndown)
  TERMINAL   - no further action possible (done + wontfix/archived/
               superseded-*) - never frontier-ready
  NON_ACTIONABLE - temporarily not claimable (blocked, triage gates)
  IN_FLIGHT  - claimed/in-progress (excluded from claimable frontier)
"""

import os
import re

DONE = {
    "resolved", "done", "completed", "complete", "closed", "merged",
    "shipped", "implemented", "landed",
}
CLOSED_EXTRA = {"wontfix", "archived"}
NON_ACTIONABLE = {
    "blocked", "on-hold", "paused", "needs-triage", "needs-info",
}
IN_FLIGHT = {"in-progress", "claimed", "wip", "doing", "active"}
TERMINAL_PREFIXES = ("superseded",)


def norm(status):
    return (status or "").strip().lower()


def is_done(status):
    return norm(status) in DONE


def is_terminal(status):
    """Leaves the work queue: done + wontfix/archived/superseded-*.
    Consumers (roadmap-board done bucket, site resolved count) use
    this as their closed predicate so both surfaces agree (#407)."""
    n = norm(status)
    return (n in DONE or n in CLOSED_EXTRA
            or any(n.startswith(p) for p in TERMINAL_PREFIXES))


def is_claimable(status):
    """Status itself permits frontier listing (blockers checked by
    caller). In-flight and non-actionable statuses are not claimable."""
    n = norm(status)
    if is_terminal(n) or n in NON_ACTIONABLE or n in IN_FLIGHT:
        return False
    return True


# Archived-effort detection (issue #406): scratch/<effort>/README.md
# must carry a real `Status: ARCHIVED` field - the word ARCHIVED
# in prose must NOT archive the effort (review finding: false
# positives silently dropped open issues from the board).
_ARCHIVED_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?\*{0,2}status\*{0,2}:?\*{0,2}"
    r"\s*[:=]?\s*archived\b")


def effort_archived(root, effort):
    if effort == "issues":
        return False
    readme = os.path.join(root, ".devin", "scratch", effort, "README.md")
    try:
        text = open(readme, encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    return bool(_ARCHIVED_RE.search(text))


def archived_efforts(root):
    """Scratch efforts marked ARCHIVED - their issues are excluded from
    live surfaces (roadmap-board, site issue ledger) so completed
    rounds stop inflating counts."""
    out = []
    scratch = os.path.join(root, ".devin", "scratch")
    if not os.path.isdir(scratch):
        return out
    for effort in sorted(os.listdir(scratch)):
        if effort_archived(root, effort):
            out.append(effort)
    return out


if __name__ == "__main__":
    import json
    print(json.dumps({
        "done": sorted(DONE),
        "closed_extra": sorted(CLOSED_EXTRA),
        "non_actionable": sorted(NON_ACTIONABLE),
        "in_flight": sorted(IN_FLIGHT),
        "terminal_prefixes": list(TERMINAL_PREFIXES),
    }, indent=2))
