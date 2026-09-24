#!/usr/bin/env python3
"""Guest-side input probe (C16 fixture).

Runs INSIDE the guest: opens /dev/input/event* read-only and appends
decoded key/button events as JSON lines to a ring file the supervisor
reads via the guest worker (exec.run cat / probe.state). Read-only:
the probe observes events; it never injects, grabs, or remaps them —
no EVIOCGRAB, no uinput writes.

Requires root or input group inside the guest; without access it
writes {"error": "probe_access_denied"} and exits 2 — a guest without
probe permission is an honest limitation, not a silent pass.
"""
import json
import os
import struct
import sys
import glob

EVENT_FMT = "llHHi"          # timeval sec/usec, type, code, value
EVENT_SIZE = struct.calcsize(EVENT_FMT)
OUT = os.environ.get("CU_PROBE_OUT", "/tmp/cu-input-probe.jsonl")
MAX_LINES = 4096


def main():
    nodes = sorted(glob.glob("/dev/input/event*"))
    if not nodes:
        print(json.dumps({"error": "no_input_devices"}))
        return 2
    fds = []
    try:
        for n in nodes:
            try:
                fds.append((n, os.open(n, os.O_RDONLY | os.O_NONBLOCK)))
            except OSError:
                pass
        if not fds:
            print(json.dumps({"error": "probe_access_denied"}))
            return 2
        print(json.dumps({"ok": True, "devices": [n for n, _ in fds],
                          "out": OUT}))
        lines = 0
        import select
        with open(OUT, "a", encoding="utf-8") as out:
            while lines < MAX_LINES:
                r, _, _ = select.select([fd for _, fd in fds],
                                        [], [], 1.0)
                for fd in r:
                    data = os.read(fd, EVENT_SIZE * 16)
                    for off in range(0, len(data) - EVENT_SIZE + 1,
                                     EVENT_SIZE):
                        sec, usec, etype, code, val = \
                            struct.unpack_from(EVENT_FMT, data, off)
                        if etype == 0:
                            continue
                        out.write(json.dumps(
                            {"t": sec + usec / 1e6, "type": etype,
                             "code": code, "value": val}) + "\n")
                        lines += 1
                out.flush()
    finally:
        for _, fd in fds:
            os.close(fd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
