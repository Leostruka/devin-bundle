#!/usr/bin/env python3
"""busybar push - focus session state -> BUSY Bar LED status display.

Spec: .devin/evals/busybar-integration/README.md (issue #450).
Device API verified: https://docs.busy.app/bar/dev/http-api
Payload shapes mirror busylib-py types.DisplayElements
(https://github.com/busy-app/busylib-py).

Connection:
  USB:      http://10.0.4.20/api   (default, no auth)
  LAN:      http://<ip>/api        (BUSYBAR_ADDR)
  Internet: https://api.busy.app/busybar + BUSYBAR_TOKEN (Bearer)

Status push is advisory: unreachable device exits 0 after a stderr
note; it never blocks a focus event. Stdlib only.

Usage:
  python extensions/busybar/push.py start --issue KEY [--effort S]
  python extensions/busybar/push.py stop
  python extensions/busybar/push.py refresh
  python extensions/busybar/push.py ping
"""
import argparse
import json
import os
import sys
import urllib.request

APP = "devin-focus"
DEFAULT_ADDR = "http://10.0.4.20/api"
TIMEOUT_S = 3


def _addr():
    return os.environ.get("BUSYBAR_ADDR", DEFAULT_ADDR).rstrip("/")


def _req(path, payload=None, method="POST"):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _addr() + path, data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    token = os.environ.get("BUSYBAR_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.status
    except OSError as e:
        print(f"busybar unreachable ({e}) - status push skipped",
              file=sys.stderr)
        return None


def _post(path, payload):
    return _req(path, payload, "POST")


def _text_el(text, display="FRONT", x=2, y=4, font="small"):
    return {"id": "status", "type": "text", "x": x, "y": y,
            "text": text, "font": font, "display": display}


def cmd_start(a):
    text = f"FOCUS {a.issue or ''}".strip()
    if a.effort:
        text += f" {a.effort}"
    return _post("/display/draw", {
        "application_name": APP,
        "elements": [_text_el(text)],
        "clear_before_draw": True,
    })


def cmd_stop(_a):
    return _post("/display/clear", {"application_name": APP})


def cmd_refresh(_a):
    # Re-emit current state from the focus ledger
    # (.devin/ledgers/focus.jsonl): pair start/stop, draw
    # "FOCUS <issue> <elapsed>" or clear. Wired when hardware exists.
    print("refresh: wire to focus ledger when hardware is available")
    return 0


def cmd_ping(_a):
    return _req("/system/status", method="GET")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start")
    p.add_argument("--issue")
    p.add_argument("--effort")
    sub.add_parser("stop")
    sub.add_parser("refresh")
    sub.add_parser("ping")
    a = ap.parse_args(argv)
    r = {"start": cmd_start, "stop": cmd_stop,
         "refresh": cmd_refresh, "ping": cmd_ping}[a.cmd](a)
    return 0 if r is None or isinstance(r, int) else 0


if __name__ == "__main__":
    sys.exit(main())
