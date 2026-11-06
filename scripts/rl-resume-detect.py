#!/usr/bin/env python3
"""Stop hook: rate-limit signature -> scheduled resume intent.

When the session ends on a provider rate-limit message, remembering "try
again later" is weak memory. This hook writes an explicit intent file
.devin/rts/intents/i<ms>.json {"kind": "resume_at", "when": <epoch>,
"auto": false} that scheduled-turns (or a human) can pick up. Opt-in:
the intent is never executed automatically.

Detection scans payload["last_assistant_message"] (and "message") for
rate-limit signatures. Reset time is parsed from common "retry after N
seconds/minutes" or HH:MM patterns when present; otherwise defaults to
now + 1h (bounded to <= 24h).

Fail-open everywhere: any exception -> exit 0 silent.
"""
import json
import os
import re
import sys
import time

RL_PATTERNS = (
    re.compile(r"rate.?limit", re.I),
    re.compile(r"\b429\b"),
    re.compile(r"quota (?:exceeded|exhausted)", re.I),
    re.compile(r"too many requests", re.I),
    re.compile(r"overloaded", re.I),
)
RETRY_AFTER_S = re.compile(
    r"retry(?:ing)? (?:after|in)\s+(\d+)\s*(?:s|sec|seconds)", re.I)
RETRY_AFTER_M = re.compile(
    r"retry(?:ing)? (?:after|in)\s+(\d+)\s*(?:m|min|minutes)", re.I)
RESET_AT = re.compile(
    r"(?:resets?|try again|retry)\s+(?:at|in)\s+(\d{1,2}):(\d{2})", re.I)


def _project_dir():
    return os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()


def _detect(text):
    if any(p.search(text) for p in RL_PATTERNS):
        return True
    return False


def _reset_ts(text):
    now = int(time.time())
    m = RETRY_AFTER_S.search(text)
    if m:
        return min(now + int(m.group(1)), now + 86400)
    m = RETRY_AFTER_M.search(text)
    if m:
        return min(now + 60 * int(m.group(1)), now + 86400)
    m = RESET_AT.search(text)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        t = time.localtime(now)
        cand = time.mktime(
            (t.tm_year, t.tm_mon, t.tm_mday, hh, mm, 0,
             t.tm_wday, t.tm_yday, t.tm_isdst))
        if cand <= now:
            cand += 86400
        return int(min(cand, now + 86400))
    return now + 3600


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    text = " ".join(str(data.get(k) or "") for k in
                    ("last_assistant_message", "message", "reason"))
    if not _detect(text):
        sys.exit(0)

    when = _reset_ts(text)
    intents = os.path.join(_project_dir(), ".devin", "rts", "intents")
    try:
        os.makedirs(intents, exist_ok=True)
        path = os.path.join(intents, "i%d.json" % int(time.time() * 1000))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({
                "kind": "resume_at",
                "when": when,
                "auto": False,
                "reason": "rate-limit signature detected at Stop",
            }, fh)
    except OSError:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext":
                "Rate-limit signature detected; resume intent written to "
                "%s (opt-in, never auto-resumed). Pick it up with "
                "scheduled-turns or run the turn manually." % path,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
