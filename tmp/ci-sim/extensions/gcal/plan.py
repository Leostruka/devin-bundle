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


def validate_inputs(tasks, slots):
    """Reject malformed input before packing (issue #409): negative or
    non-numeric minutes used to create inverted events outside free
    slots; bad ISO or missing keys leaked tracebacks. Raises ValueError
    listing every bad entry."""
    errors = []
    if not isinstance(tasks, list):
        raise ValueError("tasks must be a list")
    if not isinstance(slots, list):
        raise ValueError("slots must be a list")
    for n, t in enumerate(tasks):
        if not isinstance(t, dict):
            errors.append(f"task #{n}: not a dict")
            continue
        name = t.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"task #{n}: name must be a non-empty string")
        try:
            minutes = int(t.get("minutes"))
        except (TypeError, ValueError):
            minutes = None
        if minutes is None or minutes <= 0:
            errors.append(f"task #{n} ({name!r}): minutes must be "
                          f"an integer > 0")
        pri = t.get("priority", 99)
        if pri is not None and not isinstance(pri, int):
            errors.append(f"task #{n} ({name!r}): priority must be int")
    for n, s in enumerate(slots):
        if not isinstance(s, dict):
            errors.append(f"slot #{n}: not a dict")
            continue
        try:
            start, end = _parse(s["start"]), _parse(s["end"])
        except (KeyError, TypeError, ValueError) as e:
            errors.append(f"slot #{n}: bad start/end ({e})")
            continue
        if end <= start:
            errors.append(f"slot #{n}: end must be after start")
    if errors:
        raise ValueError("; ".join(errors))


def pack(tasks, slots):
    """Greedy first-fit by (priority, input order). Returns roteiro dict."""
    validate_inputs(tasks, slots)
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
