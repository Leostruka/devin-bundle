#!/usr/bin/env python3
"""subagent-trace - per-dispatch records + abort flags for orchestrators.

Contract (skills/dispatching-parallel-agents): the orchestrator records each
subagent dispatch at launch, updates its status on return, and checks the
abort flag between polls so a human can kill a runaway subagent.

State:
  .devin/subagent-trace.jsonl   one record per dispatch; `record` with an
                              existing id updates that line in place
  .devin/subagent-abort/<id>    abort flag file; presence = kill requested

CLI modes:
  record                       read record JSON from stdin, or build it from
                               --id/--agent/--title/--profile/--status/--notes
  --list                       print all records (JSON array)
  --pending                    print records with status "running"
  --abort ID                   create abort flag for dispatch ID
  --clear-abort ID             remove abort flag for dispatch ID
  check-abort ID               exit 0 if abort flag set, 1 otherwise

JSON envelopes; exit non-zero on {"ok": false}. Fail-open on I/O errors.
"""
import argparse
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STATUSES = ("running", "done", "killed", "timeout")


def _root():
    return os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()


def _trace_path():
    return os.path.join(_root(), ".devin", "subagent-trace.jsonl")


def _abort_dir():
    return os.path.join(_root(), ".devin", "subagent-abort")


def _abort_path(rid):
    return os.path.join(_abort_dir(), rid)


def _load(path):
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def _save(path, recs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _record(args, piped=None):
    try:
        _recfg = getattr(sys.stdin, "reconfigure", None)
        if _recfg:
            try:
                _recfg(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
        if piped is not None:
            payload = json.loads(piped)
        elif not sys.stdin.isatty():
            payload = json.load(sys.stdin)
        else:
            payload = {}
    except (ValueError, OSError):
        payload = {}
    rec = dict(payload) if isinstance(payload, dict) else {}
    for k in ("id", "agent", "title", "profile", "status", "notes"):
        v = getattr(args, k, None)
        if v is not None:
            rec[k] = v
    if not rec.get("id"):
        rec["id"] = f"s{int(time.time() * 1000)}"
    rec.setdefault("status", "running")
    if rec["status"] not in STATUSES:
        print(json.dumps({"ok": False,
                          "error": f"status must be one of {STATUSES}"}))
        return 2
    path = _trace_path()
    recs = _load(path)
    now = int(time.time())
    for r in recs:
        if r.get("id") == rec["id"]:
            rec.setdefault("ts", r.get("ts", now))
            rec["updated"] = now
            r.update(rec)
            break
    else:
        rec.setdefault("ts", now)
        recs.append(rec)
    _save(path, recs)
    print(json.dumps({"ok": True, "id": rec["id"], "record": rec}))
    return 0


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    p = argparse.ArgumentParser(prog="subagent-trace")
    p.add_argument("mode", nargs="?", default=None,
                   choices=["record", "check-abort"])
    p.add_argument("id_arg", nargs="?", default=None)
    p.add_argument("--id", dest="id", default=None)
    p.add_argument("--agent", default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--profile", default=None)
    p.add_argument("--status", default=None)
    p.add_argument("--notes", default=None)
    p.add_argument("--list", action="store_true")
    p.add_argument("--pending", action="store_true")
    p.add_argument("--abort", default=None)
    p.add_argument("--clear-abort", dest="clear_abort", default=None)
    args = p.parse_args(argv[1:])
    try:
        return _main(args)
    except Exception as e:  # fail-open
        print(json.dumps({"ok": False, "error": str(e)}))
        return 0


def _main(args):
    path = _trace_path()
    if args.list or args.pending:
        recs = _load(path)
        if args.pending:
            recs = [r for r in recs if r.get("status") == "running"]
        print(json.dumps({"ok": True, "pending": len(recs),
                          "records": recs}, indent=1))
        return 0
    if args.abort is not None:
        os.makedirs(_abort_dir(), exist_ok=True)
        with open(_abort_path(args.abort), "w", encoding="utf-8") as f:
            json.dump({"id": args.abort, "ts": int(time.time())}, f)
        print(json.dumps({"ok": True, "aborted": args.abort}))
        return 0
    if args.clear_abort is not None:
        try:
            os.remove(_abort_path(args.clear_abort))
            removed = True
        except OSError:
            removed = False
        print(json.dumps({"ok": True, "cleared": args.clear_abort,
                          "removed": removed}))
        return 0
    if args.mode == "check-abort":
        rid = args.id_arg or args.id
        if not rid:
            print(json.dumps({"ok": False,
                              "error": "check-abort <id>"}))
            return 2
        aborted = os.path.exists(_abort_path(rid))
        print(json.dumps({"ok": True, "id": rid, "abort": aborted}))
        return 0 if aborted else 1
    if args.mode == "record":
        return _record(args)
    # no args: treat piped non-empty stdin as a record payload
    try:
        _recfg = getattr(sys.stdin, "reconfigure", None)
        if _recfg:
            try:
                _recfg(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            if data.strip():
                return _record(args, piped=data)
    except OSError:
        pass
    print(json.dumps({"ok": False,
                      "error": "usage: record|--list|--pending|--abort ID|"
                               "--clear-abort ID|check-abort ID"}))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
