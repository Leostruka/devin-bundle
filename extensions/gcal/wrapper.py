#!/usr/bin/env python3
"""gcal wrapper: free/busy + roteiro planning + event writer CLI.

Subcommands:
  free-busy --ics FILE | --ics-url URL | --caldav | [--calendars id[,id]] [--from ISO --to ISO]
  plan      --tasks FILE.json (--ics FILE | --ics-url URL | --slots FILE.json | --caldav)
            [--from ISO --to ISO]
  add       --summary X --start ISO --end ISO [--calendar NAME-or-id]
            [--desc X] [--loc X] [--tz Zone] [--caldav] --confirm
  apply     --roteiro FILE.json [--calendar NAME-or-id] [--prefix X]
            [--caldav] --confirm
  doctor    config presence report (never prints secrets)

Backends: default Google Calendar (BUNDLE_GCAL_* / credentials.toml
[gcal]); --caldav selects CalDAV (BUNDLE_CALDAV_URL/USER/PASSWORD or
[caldav] in credentials.toml) - app-password servers like iCloud,
Fastmail, Nextcloud, Radicale. --ics stays the offline dev path.

Writes need --confirm: without it the CLI prints the payload and exits
0 with status "confirm-required" (never calls the API).
Default --calendar is AGdevin: a dedicated agent calendar, created on
first write and reused after (isolation from the account's other
calendars). Pass 'primary' or a raw calendar id to override.

Output: JSON envelope {status, ...}. Exit 0 = ok.
Defaults: --from today 08:00 local-naive-UTC, --to same day 20:00.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caldav  # noqa: E402
import gcal  # noqa: E402
import plan  # noqa: E402


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False,
              default=str)
    sys.stdout.write("\n")
    sys.exit(code)


VALUE_FLAGS = {
    "--ics", "--ics-url", "--calendars", "--from", "--to", "--tasks",
    "--slots", "--summary", "--start", "--end", "--calendar", "--desc",
    "--loc", "--tz", "--roteiro", "--prefix",
}
BOOL_FLAGS = {"--caldav", "--confirm"}
KNOWN_FLAGS = VALUE_FLAGS | BOOL_FLAGS


def _normalize(argv):
    """Split --flag=value into --flag value; reject unknown --* tokens
    and flags missing a value (issue #413: silent wrong-window bugs)."""
    out = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--") and "=" in tok:
            k, v = tok.split("=", 1)
            if k not in KNOWN_FLAGS:
                emit({"status": "error",
                      "stderr": f"unknown flag: {k}"}, 2)
            out += [k, v]
        elif tok.startswith("--"):
            if tok not in KNOWN_FLAGS:
                emit({"status": "error",
                      "stderr": f"unknown flag: {tok}"}, 2)
            out.append(tok)
        else:
            out.append(tok)
        i += 1
    # value flags must be followed by a non-flag token
    for j, tok in enumerate(out):
        if tok in VALUE_FLAGS:
            if j + 1 >= len(out) or out[j + 1].startswith("--"):
                emit({"status": "error",
                      "stderr": f"flag {tok} needs a value"}, 2)
    return out


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
    dav = caldav.load_credentials()
    gcal_env = bool(os.environ.get("BUNDLE_GCAL_CLIENT_ID"))
    caldav_env = bool(os.environ.get("BUNDLE_CALDAV_URL"))
    emit({
        "status": "ok" if (creds or dav) else "missing",
        "credentials": {
            "gcal": {"env": gcal_env,
                     "credentials_toml": bool(creds and not gcal_env)},
            "caldav": {"env": caldav_env,
                       "credentials_toml": bool(dav and not caldav_env)},
        },
        "ics_dev_mode": True,
        "hint": (None if (creds or dav) else
                 "set BUNDLE_GCAL_* / [gcal] for Google Calendar, or "
                 "BUNDLE_CALDAV_URL/USER/PASSWORD / [caldav] for CalDAV "
                 "(app-password servers); --ics works offline. "
                 "writes need --confirm"),
    }, 0 if (creds or dav) else 1)


def _ics_result(text, src):
    """ics_busy dict -> (busy, all_day, extras) for _busy_from_source."""
    res = gcal.ics_busy(text)
    extras = {}
    if res["recurring"]:
        extras["recurring_events"] = res["recurring"]
        extras["hint"] = ("RRULE not expanded: recurring events "
                          "contribute only their first instance")
    if res["warnings"]:
        extras["warnings"] = res["warnings"]
    if res["all_day"]:
        extras["all_day"] = res["all_day"]
    return res["busy"], extras


def _busy_from_source(argv):
    """Return (busy, source, all_day, extras) or emit missing."""
    ics = _arg(argv, "--ics")
    if ics:
        if not os.path.isfile(ics):
            emit({"status": "error",
                  "stderr": f"ics file not found: {ics}"}, 2)
        busy, extras = _ics_result(
            open(ics, encoding="utf-8", errors="replace").read(), "ics")
        return busy, "ics", extras.get("all_day"), extras
    ics_url = _arg(argv, "--ics-url")
    if ics_url:
        if not ics_url.startswith(("http://", "https://")):
            emit({"status": "error",
                  "stderr": "--ics-url must be http(s)"}, 2)
        try:
            with urllib.request.urlopen(
                    ics_url, timeout=gcal.HTTP_TIMEOUT) as resp:
                text = resp.read().decode("utf-8", "replace")
        except Exception as e:
            emit({"status": "error",
                  "stderr": f"ics-url fetch failed: {e}"}, 1)
        busy, extras = _ics_result(text, "ics-url")
        return busy, "ics-url", extras.get("all_day"), extras
    if "--caldav" in argv:
        creds = caldav.load_credentials()
        if not creds:
            emit({"status": "missing",
                  "stderr": "no caldav credentials; set "
                            "BUNDLE_CALDAV_URL/USER/PASSWORD or "
                            "credentials.toml [caldav]"}, 1)
        names = [c.strip() for c in
                 (_arg(argv, "--calendars") or "").split(",") if c.strip()]
        tmin, tmax = _day_range(argv)
        try:
            return (caldav.free_busy(creds, calendars=names or None,
                                     tmin=tmin, tmax=tmax),
                    "caldav", None, None)
        except Exception as e:
            emit({"status": "error",
                  "stderr": f"caldav free-busy failed: {e}"}, 1)
    creds = gcal.load_credentials()
    if not creds:
        emit({"status": "missing",
              "stderr": "no gcal credentials; use --ics for dev mode, "
                        "--caldav for CalDAV, or set BUNDLE_GCAL_* / "
                        "credentials.toml [gcal]"}, 1)
    cals = (_arg(argv, "--calendars", "primary") or "primary").split(",")
    tmin, tmax = _day_range(argv)
    try:
        token = gcal.access_token(creds)
        res = gcal.free_busy(token, [c.strip() for c in cals],
                             tmin, tmax)
        return res["busy"], "api", res["all_day"], None
    except Exception as e:  # network/HTTP/JSON failures -> error env
        emit({"status": "error", "stderr": f"free-busy failed: {e}"}, 1)


def cmd_free_busy(argv):
    tmin, tmax = _day_range(argv)
    busy, src, all_day, extras = _busy_from_source(argv)
    out = {"status": "ok", "source": src, "from": tmin, "to": tmax,
           "busy": busy,
           "free_slots": gcal.free_slots(busy, tmin, tmax)}
    if all_day:
        out["all_day"] = all_day
    if extras:
        for k in ("recurring_events", "hint", "warnings"):
            if k in extras:
                out[k] = extras[k]
    emit(out)


def cmd_plan(argv):
    tasks_file = _arg(argv, "--tasks")
    if not tasks_file or not os.path.isfile(tasks_file):
        emit({"status": "error",
              "stderr": "--tasks FILE.json required"}, 2)
    try:
        with open(tasks_file, encoding="utf-8") as fh:
            tasks = json.loads(fh.read())
    except (OSError, ValueError) as e:
        emit({"status": "error", "stderr": f"bad tasks file: {e}"}, 2)
    slots_file = _arg(argv, "--slots")
    extras = None
    if slots_file:
        try:
            with open(slots_file, encoding="utf-8") as fh:
                slots = json.loads(fh.read())
        except (OSError, ValueError) as e:
            emit({"status": "error", "stderr": f"bad slots file: {e}"}, 2)
        if isinstance(slots, dict):
            slots = slots.get("free_slots", [])
    else:
        tmin, tmax = _day_range(argv)
        busy, _, _, extras = _busy_from_source(argv)
        slots = gcal.free_slots(busy, tmin, tmax)
    try:
        roteiro = plan.pack(tasks, slots)
    except ValueError as e:
        emit({"status": "error", "stderr": f"bad plan input: {e}"}, 2)
    out = {"status": "ok", "roteiro": roteiro}
    if extras:
        for k in ("recurring_events", "hint", "warnings"):
            if k in extras:
                out[k] = extras[k]
    emit(out)


def _write_creds():
    creds = gcal.load_credentials()
    if not creds:
        emit({"status": "missing",
              "stderr": "no gcal credentials; set BUNDLE_GCAL_* or "
                        "credentials.toml [gcal] (refresh token must "
                        "carry calendar.events scope for writes)"}, 1)
    return creds


def _caldav_creds_or_emit():
    creds = caldav.load_credentials()
    if not creds:
        emit({"status": "missing",
              "stderr": "no caldav credentials; set BUNDLE_CALDAV_* or "
                        "credentials.toml [caldav]"}, 1)
    return creds


def _cmd_add_caldav(argv, summary, start, end, calendar):
    try:
        ics = caldav.event_ics(
            summary, start, end, description=_arg(argv, "--desc"),
            location=_arg(argv, "--loc"))
    except Exception as e:
        emit({"status": "error", "stderr": f"bad datetime: {e}"}, 2)
    if "--confirm" not in argv:
        emit({"status": "confirm-required", "backend": "caldav",
              "calendar": calendar,
              "events": [{"summary": summary, "start": start,
                          "end": end, "ics": ics}],
              "hint": "re-run with --confirm to write"})
    creds = _caldav_creds_or_emit()
    try:
        href, created_cal = caldav.ensure_calendar(creds, calendar)
        created = caldav.create_event(creds, href, ics)
    except Exception as e:
        emit({"status": "error", "stderr": f"caldav add failed: {e}"}, 1)
    emit({"status": "ok", "backend": "caldav", "calendar": href,
          "calendar_created": created_cal, "event": created})


def _validated_schedule(schedule):
    """Ensure schedule is a list of dicts with start/end (issue #395:
    non-dict blocks used to crash with AttributeError tracebacks)."""
    if not isinstance(schedule, list):
        emit({"status": "error",
              "stderr": "schedule must be a list of blocks"}, 2)
    for n, block in enumerate(schedule):
        if (not isinstance(block, dict)
                or "start" not in block or "end" not in block):
            emit({"status": "error",
                  "stderr": f"bad block #{n}: need dict with "
                            f"start/end, got {block!r}"}, 2)
    return schedule


def _cmd_apply_caldav(argv, schedule, calendar, prefix):
    schedule = _validated_schedule(schedule)
    events = []
    for block in schedule:
        try:
            ics = caldav.event_ics(
                prefix + str(block.get("task", "block")),
                block["start"], block["end"],
                description="roteiro block")
        except (KeyError, TypeError, ValueError) as e:
            emit({"status": "error",
                  "stderr": f"bad block {block}: {e}"}, 2)
        events.append({"task": prefix + str(block.get("task", "block")),
                       "start": block["start"], "end": block["end"],
                       "ics": ics})
    if "--confirm" not in argv:
        emit({"status": "confirm-required", "backend": "caldav",
              "calendar": calendar, "events": events,
              "hint": "re-run with --confirm to write"})
    creds = _caldav_creds_or_emit()
    try:
        href, created_cal = caldav.ensure_calendar(creds, calendar)
    except Exception as e:
        emit({"status": "error",
              "stderr": f"caldav calendar failed: {e}"}, 1)
    created, failed = [], []
    for ev in events:
        try:
            created.append({"task": ev["task"],
                            **caldav.create_event(creds, href, ev["ics"])})
        except Exception as e:
            failed.append({"summary": ev["task"], "stderr": str(e)})
    emit({"status": "ok" if not failed else "partial",
          "backend": "caldav", "calendar": href,
          "calendar_created": created_cal,
          "created": created, "failed": failed},
         0 if not failed else 1)


def cmd_add(argv):
    summary = _arg(argv, "--summary")
    start = _arg(argv, "--start")
    end = _arg(argv, "--end")
    if not (summary and start and end):
        emit({"status": "error",
              "stderr": "add needs --summary X --start ISO --end ISO"}, 2)
    calendar = _arg(argv, "--calendar", gcal.AGENT_CALENDAR)
    if "--caldav" in argv:
        return _cmd_add_caldav(argv, summary, start, end, calendar)
    try:
        payload = gcal.event_payload(
            summary, start, end, description=_arg(argv, "--desc"),
            location=_arg(argv, "--loc"), tz=_arg(argv, "--tz"))
    except ValueError as e:
        emit({"status": "error", "stderr": f"bad datetime: {e}"}, 2)
    if "--confirm" not in argv:
        emit({"status": "confirm-required", "calendar": calendar,
              "payload": payload,
              "hint": "re-run with --confirm to write"})
    try:
        token = gcal.access_token(_write_creds())
        cid, created_cal = gcal.resolve_calendar(token, calendar)
        created = gcal.create_event(token, cid, payload)
    except Exception as e:
        emit({"status": "error", "stderr": f"add failed: {e}"}, 1)
    emit({"status": "ok", "calendar": cid,
          "calendar_created": created_cal, "event": created})


def cmd_apply(argv):
    roteiro_file = _arg(argv, "--roteiro")
    if not roteiro_file or not os.path.isfile(roteiro_file):
        emit({"status": "error",
              "stderr": "--roteiro FILE.json required"}, 2)
    try:
        with open(roteiro_file, encoding="utf-8") as fh:
            data = json.loads(fh.read())
    except (OSError, ValueError) as e:
        emit({"status": "error", "stderr": f"bad roteiro file: {e}"}, 2)
    if isinstance(data, dict):
        inner = data.get("roteiro")
        schedule = (inner.get("schedule") if isinstance(inner, dict)
                    else data.get("schedule", []))
    else:
        schedule = data
    schedule = _validated_schedule(schedule)
    calendar = _arg(argv, "--calendar", gcal.AGENT_CALENDAR)
    prefix = _arg(argv, "--prefix", "")
    if "--caldav" in argv:
        return _cmd_apply_caldav(argv, schedule, calendar, prefix)
    payloads = []
    for block in schedule:
        try:
            payloads.append(gcal.event_payload(
                prefix + str(block.get("task", "block")),
                block["start"], block["end"],
                description="roteiro block"))
        except (KeyError, TypeError, ValueError) as e:
            emit({"status": "error",
                  "stderr": f"bad block {block}: {e}"}, 2)
    if "--confirm" not in argv:
        emit({"status": "confirm-required", "calendar": calendar,
              "events": payloads,
              "hint": "re-run with --confirm to write"})
    try:
        token = gcal.access_token(_write_creds())
        cid, created_cal = gcal.resolve_calendar(token, calendar)
    except Exception as e:
        emit({"status": "error", "stderr": f"calendar failed: {e}"}, 1)
    created, failed = [], []
    for p in payloads:
        try:
            created.append(gcal.create_event(token, cid, p))
        except Exception as e:
            failed.append({"summary": p["summary"], "stderr": str(e)})
    emit({"status": "ok" if not failed else "partial",
          "calendar": cid, "calendar_created": created_cal,
          "created": created, "failed": failed},
         0 if not failed else 1)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        emit({"usage": "wrapper.py <free-busy|plan|add|apply|doctor> "
                       "[args]",
              "subcommands": ["free-busy", "plan", "add", "apply",
                              "doctor"]},
             0 if argv else 2)
    argv = [argv[0]] + _normalize(argv[1:])
    if argv[0] == "doctor":
        cmd_doctor()
    elif argv[0] == "free-busy":
        cmd_free_busy(argv[1:])
    elif argv[0] == "plan":
        cmd_plan(argv[1:])
    elif argv[0] == "add":
        cmd_add(argv[1:])
    elif argv[0] == "apply":
        cmd_apply(argv[1:])
    else:
        emit({"status": "rejected",
              "stderr": f"unknown subcommand: {argv[0]}"}, 2)


if __name__ == "__main__":
    main()
