#!/usr/bin/env python3
"""focus - pomodoro-style focus-session tracker (issue #419, #346 micro).

Append-only JSONL ledger at .devin/ledgers/focus.jsonl (gitignored, same
pattern as metrics.jsonl). Records pair start->stop into sessions; report
aggregates focus minutes per day and per issue. Offline, stdlib only.

Usage:
  python scripts/focus.py [--root DIR] start [--issue KEY]
      [--effort SLUG] [--note TXT]
  python scripts/focus.py [--root DIR] stop [--note TXT]
  python scripts/focus.py [--root DIR] report [--day YYYY-MM-DD] [--json]
  python scripts/focus.py [--root DIR] status

--root defaults to DEVIN_PROJECT_DIR or cwd (same as roadmap-board).
"""
import argparse
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


_ROOT = None


def ledger_path():
    project = _ROOT or os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    return os.path.join(project, ".devin", "ledgers", "focus.jsonl")


def _append(rec):
    path = ledger_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rec = {"t": int(time.time()), **rec}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def _events():
    path = ledger_path()
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _sessions(events):
    """Pair start->stop FIFO. Returns (sessions, open_session|None)."""
    sessions, open_s = [], None
    for e in events:
        ev = e.get("event")
        if ev == "start":
            if open_s is not None:  # unclosed previous - close it stale
                sessions.append({**open_s, "end": e["t"],
                                 "stale": True})
            open_s = e
        elif ev == "stop" and open_s is not None:
            sessions.append({**open_s, "end": e["t"],
                             "note": e.get("note")})
            open_s = None
    return sessions, open_s


def cmd_start(a):
    events = _events()
    _, open_s = _sessions(events)
    if open_s is not None:
        print(f"session already open since "
              f"{time.strftime('%H:%M', time.localtime(open_s['t']))} "
              f"(issue={open_s.get('issue') or '-'}) - run `stop` first",
              file=sys.stderr)
        return 1
    rec = _append({"event": "start", "issue": a.issue,
                   "effort": a.effort, "note": a.note})
    print(f"focus start {time.strftime('%Y-%m-%d %H:%M')} "
          f"issue={a.issue or '-'} effort={a.effort or '-'}")
    return 0


def cmd_stop(a):
    events = _events()
    sessions, open_s = _sessions(events)
    if open_s is None:
        print("no open focus session", file=sys.stderr)
        return 1
    dur = max(0, int(time.time()) - int(open_s["t"]))
    _append({"event": "stop", "note": a.note})
    print(f"focus stop - session {dur // 60}min{dur % 60:02d}s "
          f"(issue={open_s.get('issue') or '-'})")
    return 0


def _day(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def cmd_report(a):
    sessions, open_s = _sessions(_events())
    rows = []
    for s in sessions:
        day = _day(s["t"])
        if a.day and day != a.day:
            continue
        rows.append({
            "day": day,
            "issue": s.get("issue"),
            "effort": s.get("effort"),
            "start": s["t"], "end": s.get("end"),
            "min": round((s.get("end", s["t"]) - s["t"]) / 60, 1),
            "stale": bool(s.get("stale")),
            "note": s.get("note"),
        })
    if a.json:
        print(json.dumps({"sessions": rows,
                          "open": ({"issue": open_s.get("issue"),
                                    "since": open_s["t"]}
                                   if open_s else None)},
                         ensure_ascii=False, indent=1))
        return 0
    if not rows and open_s is None:
        print("no focus sessions recorded")
        return 0
    by_day, by_issue = {}, {}
    for r in rows:
        by_day[r["day"]] = by_day.get(r["day"], 0) + r["min"]
        key = r["issue"] or "(untracked)"
        by_issue[key] = by_issue.get(key, 0) + r["min"]
    print("per day:")
    for d in sorted(by_day):
        print(f"  {d}  {by_day[d]:6.1f} min")
    print("per issue:")
    for k in sorted(by_issue, key=lambda x: -by_issue[x]):
        print(f"  {by_issue[k]:6.1f} min  {k}")
    if open_s is not None:
        print(f"OPEN session since "
              f"{time.strftime('%H:%M', time.localtime(open_s['t']))} "
              f"issue={open_s.get('issue') or '-'}")
    return 0


def cmd_status(_a):
    _, open_s = _sessions(_events())
    if open_s is None:
        print("no open focus session")
    else:
        print(f"open since {time.strftime('%Y-%m-%d %H:%M', time.localtime(open_s['t']))} "
              f"issue={open_s.get('issue') or '-'} effort={open_s.get('effort') or '-'}")
    return 0


def main(argv=None):
    global _ROOT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None,
                    help="project root (default: DEVIN_PROJECT_DIR or cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start")
    p.add_argument("--issue"); p.add_argument("--effort")
    p.add_argument("--note")
    p = sub.add_parser("stop"); p.add_argument("--note")
    p = sub.add_parser("report")
    p.add_argument("--day"); p.add_argument("--json", action="store_true")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    _ROOT = a.root
    return {"start": cmd_start, "stop": cmd_stop,
            "report": cmd_report, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
