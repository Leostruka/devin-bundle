"""world_bridge - reuse rtsd's event-sourced world model (GDD D1/D4).

Imports extensions/rtsd/world.py unchanged so agent-rts projects the
identical world (heroes, buildings, orders, fog) from the same
.devin/rts/events.jsonl. Repo telemetry is layered on top in the server
snapshot; World.apply stays pure (replay determinism preserved).

Tailing: rts-emit.py appends events.jsonl directly when no daemon answers,
and rtsd appends when it is the one running. Either way the file is the
durable log; tail_new() applies lines added since our last offset.
"""
import json
import os
import sys

_RTSD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "rtsd")
if _RTSD not in sys.path:
    sys.path.insert(0, os.path.abspath(_RTSD))

import world as worldmod  # noqa: E402

EVENTS = "events.jsonl"


def state_dir(root):
    d = os.path.join(root, ".devin", "rts")
    for sub in ("", "decisions", "intents", "agents"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d


def open_world(root, replay_events=None):
    """Replay the durable log into a World. replay_events lets the server
    replay a foreign file (--replay) instead of the live log."""
    path = replay_events or os.path.join(state_dir(root), EVENTS)
    w = worldmod.World.replay_file(root, path)
    try:
        offset = os.path.getsize(path)
    except OSError:
        offset = 0
    return w, offset


def tail_new(world, path, offset):
    """Apply log lines appended since offset. Returns (events, offset);
    skips a trailing partial line (writer mid-append)."""
    evs = []
    try:
        size = os.path.getsize(path)
        if size < offset:      # log rotated/truncated
            offset = 0
        if size == offset:
            return evs, offset
        with open(path, "rb") as f:
            f.seek(offset)
            raw = f.read()
    except OSError:
        return evs, offset
    cut = raw.rfind(b"\n")
    if cut < 0:
        return evs, offset     # no complete line yet
    offset += cut + 1
    for ln in raw[:cut].decode("utf-8", "replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            evs.append(json.loads(ln))
        except Exception:
            pass
    for ev in evs:
        try:
            world.apply(ev)
        except Exception:
            pass
    return evs, offset
