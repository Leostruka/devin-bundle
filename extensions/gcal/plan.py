#!/usr/bin/env python3
"""roteiro planner: pack tasks into free slots (issue #345).

Deterministic greedy packer - no model in the loop:
  - tasks: [{name, minutes, priority}]  (priority: lower number = earlier)
  - slots: [{start, end}] ISO intervals (from gcal.free_slots / ics)
  - atomic blocks: a task is placed whole or flagged unscheduled
Output roteiro JSON: {schedule:[{task,start,end}], unscheduled:[...],
slack_min}.
"""
from datetime import datetime, timedelta


def _parse(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _iso(dt):
    return dt.isoformat()


def pack(tasks, slots):
    """Greedy first-fit by (priority, input order). Returns roteiro dict."""
    remaining = [(_parse(s["start"]), _parse(s["end"]))
                 for s in sorted(slots, key=lambda s: s["start"])]
    order = sorted(enumerate(tasks),
                   key=lambda it: (it[1].get("priority", 99), it[0]))
    schedule, unscheduled = [], []
    for _, t in order:
        need = int(t["minutes"])
        placed = False
        for i, (s, e) in enumerate(remaining):
            if (e - s).total_seconds() / 60 >= need:
                end = s + timedelta(minutes=need)
                schedule.append({"task": t["name"],
                                 "start": _iso(s), "end": _iso(end)})
                remaining[i] = (end, e)
                placed = True
                break
        if not placed:
            unscheduled.append(t["name"])
    slack = sum((e - s).total_seconds() / 60
                for s, e in remaining if e > s)
    return {"schedule": schedule,
            "unscheduled": unscheduled,
            "slack_min": int(slack),
            "overcommit": bool(unscheduled)}
