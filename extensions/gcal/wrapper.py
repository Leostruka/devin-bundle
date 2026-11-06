#!/usr/bin/env python3
"""gcal wrapper: free/busy + roteiro planning CLI.

Subcommands:
  free-busy --ics FILE | --calendars id[,id] [--from ISO --to ISO]
  plan      --tasks FILE.json (--ics FILE | --slots FILE.json)
            [--from ISO --to ISO]
  doctor    config presence report (never prints secrets)

Output: JSON envelope {status, ...}. Exit 0 = ok.
Defaults: --from today 08:00 local-naive-UTC, --to same day 20:00.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcal  # noqa: E402
import plan  # noqa: E402


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False,
              default=str)
    sys.stdout.write("\n")
    sys.exit(code)


def _arg(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def _day_range(argv):
    now = datetime.now(timezone.utc)
    tmin = _arg(argv, "--from",
                now.replace(hour=8, minute=0, second=0,
                            microsecond=0).isoformat())
    tmax = _arg(argv, "--to",
                now.replace(hour=20, minute=0, second=0,
                            microsecond=0).isoformat())
    return tmin, tmax


def cmd_doctor():
    creds = gcal.load_credentials()
    emit({
        "status": "ok" if creds else "missing",
        "credentials": {
            "env": bool(os.environ.get("BUNDLE_GCAL_CLIENT_ID")),
            "credentials_toml": bool(
                creds and not os.environ.get("BUNDLE_GCAL_CLIENT_ID")),
        },
        "ics_dev_mode": True,
        "hint": (None if creds else
                 "set BUNDLE_GCAL_CLIENT_ID/SECRET/REFRESH_TOKEN or "
                 "[gcal] in credentials.toml; --ics works offline"),
    }, 0 if creds else 1)


def _busy_from_source(argv):
    """Return (busy, source) or emit missing."""
    ics = _arg(argv, "--ics")
    if ics:
        if not os.path.isfile(ics):
            emit({"status": "error",
                  "stderr": f"ics file not found: {ics}"}, 2)
        return gcal.ics_busy(
            open(ics, encoding="utf-8", errors="replace").read()), "ics"
    creds = gcal.load_credentials()
    if not creds:
        emit({"status": "missing",
              "stderr": "no gcal credentials; use --ics for dev mode or "
                        "set BUNDLE_GCAL_* / credentials.toml [gcal]"}, 1)
    cals = (_arg(argv, "--calendars", "primary") or "primary").split(",")
    tmin, tmax = _day_range(argv)
    try:
        token = gcal.access_token(creds)
        return gcal.free_busy(token, [c.strip() for c in cals],
                              tmin, tmax), "api"
    except Exception as e:  # network/HTTP/JSON failures -> error env
        emit({"status": "error", "stderr": f"free-busy failed: {e}"}, 1)


def cmd_free_busy(argv):
    tmin, tmax = _day_range(argv)
    busy, src = _busy_from_source(argv)
    emit({"status": "ok", "source": src, "from": tmin, "to": tmax,
          "busy": busy,
          "free_slots": gcal.free_slots(busy, tmin, tmax)})


def cmd_plan(argv):
    tasks_file = _arg(argv, "--tasks")
    if not tasks_file or not os.path.isfile(tasks_file):
        emit({"status": "error",
              "stderr": "--tasks FILE.json required"}, 2)
    tasks = json.loads(open(tasks_file, encoding="utf-8").read())
    slots_file = _arg(argv, "--slots")
    if slots_file:
        slots = json.loads(open(slots_file, encoding="utf-8").read())
        if isinstance(slots, dict):
            slots = slots.get("free_slots", [])
    else:
        tmin, tmax = _day_range(argv)
        busy, _ = _busy_from_source(argv)
        slots = gcal.free_slots(busy, tmin, tmax)
    emit({"status": "ok", "roteiro": plan.pack(tasks, slots)})


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        emit({"usage": "wrapper.py <free-busy|plan|doctor> [args]",
              "subcommands": ["free-busy", "plan", "doctor"]},
             0 if argv else 2)
    if argv[0] == "doctor":
        cmd_doctor()
    elif argv[0] == "free-busy":
        cmd_free_busy(argv[1:])
    elif argv[0] == "plan":
        cmd_plan(argv[1:])
    else:
        emit({"status": "rejected",
              "stderr": f"unknown subcommand: {argv[0]}"}, 2)


if __name__ == "__main__":
    main()
