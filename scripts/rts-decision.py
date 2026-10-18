#!/usr/bin/env python3
"""rts-decision - decision bridge between Devin CLI and the RTS overlay UI.

Stdin payload for --create (JSON):
  {"kind": "permission|question|merge", "prompt": "...", "options": [...],
   "timeout": 120}

Modes:
  --create            writes <cwd>/.devin/rts/decisions/<id>.json (pending),
                      prints the id to stdout.
  --wait <id>         polls the decision file for status=="answered" (set when
                      the UI POSTs /decisions/<id>/answer to rtsd). Prints
                      {"status":"answered","choice":i,"text":...} on stdout.
                      On timeout or infra error prints
                      {"status":"timeout","choice":<deny_index>} - fails CLOSED:
                      the last option is assumed to be the safe default (deny).
  --create --wait     create then wait in one call.

Exit codes: 0 always for --create errors (fail-open: decision simply isn't
surfaced); --wait always prints a resolution and exits 0 so hook callers get
a parseable answer.
"""
import json
import os
import sys
import time

DEFAULT_OPTIONS = ["allow", "deny"]
POLL = 0.5


def decisions_dir():
    d = os.path.join(os.getcwd(), ".devin", "rts", "decisions")
    os.makedirs(d, exist_ok=True)
    return d


def create(spec):
    did = "d%d" % int(time.time() * 1000)
    d = {
        "id": did,
        "kind": spec.get("kind", "question"),
        "prompt": spec.get("prompt", ""),
        "options": spec.get("options") or list(DEFAULT_OPTIONS),
        "status": "pending",
        "created_at": time.time(),
        "timeout": spec.get("timeout", 120),
    }
    path = os.path.join(decisions_dir(), did + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return did


def wait(did, timeout):
    path = os.path.join(decisions_dir(), did + ".json")
    rpath = path + ".response"
    deadline = time.time() + timeout
    grace = time.time() + 2
    while time.time() < deadline:
        if time.time() < grace or os.path.isfile(path):
            pass
        else:
            print(json.dumps({"status": "error", "choice": -1,
                              "reason": "unknown decision id"}))
            return
        try:
            if os.path.isfile(rpath):
                with open(rpath, encoding="utf-8") as f:
                    ans = json.load(f)
                ans["status"] = "answered"
                print(json.dumps(ans, ensure_ascii=False))
                return
        except Exception:
            pass
        time.sleep(POLL)
    # fail closed: last option = safe default (deny)
    deny = len(DEFAULT_OPTIONS) - 1
    try:
        with open(path, encoding="utf-8") as f:
            deny = len(json.load(f).get("options", DEFAULT_OPTIONS)) - 1
    except Exception:
        pass
    print(json.dumps({"status": "timeout", "choice": deny},
                     ensure_ascii=False))


def main():
    args = sys.argv[1:]
    do_create = "--create" in args
    do_wait = "--wait" in args
    if do_create:
        try:
            raw = sys.stdin.read()
            spec = json.loads(raw) if raw.strip() else {}
        except Exception:
            spec = {}
        try:
            did = create(spec)
        except Exception:
            sys.exit(0)
        if not do_wait:
            print(did)
            return
        timeout = spec.get("timeout", 120)
    else:
        did = None
        timeout = 120
    if do_wait:
        if not did:
            try:
                did = args[args.index("--wait") + 1]
            except IndexError:
                print(json.dumps({"status": "error", "choice": -1}))
                return
            try:
                with open(os.path.join(decisions_dir(), did + ".json"),
                          encoding="utf-8") as f:
                    timeout = json.load(f).get("timeout", 120)
            except Exception:
                pass
        wait(did, timeout)
        return
    if not do_create:
        print(__doc__)
    sys.exit(0)


if __name__ == "__main__":
    main()
