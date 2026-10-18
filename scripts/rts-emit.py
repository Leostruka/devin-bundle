#!/usr/bin/env python3
"""rts-emit - PostToolUse/lifecycle event tap for the RTS overlay (rtsd).

Stdin payload (Devin CLI hook protocol):
  {"hook_event_name": "PostToolUse"|"UserPromptSubmit"|...,
   "tool_name": "...", "tool_input": {...}, "session_id": "...",
   "prompt_id": "..."}

Behavior: wrap the payload as an RTS event and POST it to the local rtsd
daemon (http://127.0.0.1:$RTSD_PORT/event, default port 8797, timeout 0.3s).
If the daemon is offline or any error occurs, append the event directly to
<cwd>/.devin/rts/events.jsonl so the record survives for replay.

Exit codes: always 0 (fail-open). Never prints to stdout: hook stdout is
reserved for protocol JSON.
"""
import json
import os
import sys
import time
import urllib.request

TIMEOUT = 0.3


def port():
    try:
        return int(os.environ.get("RTSD_PORT", "8797"))
    except (TypeError, ValueError):
        return 8797


def event(payload):
    return {
        "type": "hook." + str(payload.get("hook_event_name", "unknown")).lower(),
        "hook": payload.get("hook_event_name"),
        "tool": payload.get("tool_name"),
        "session_id": payload.get("session_id"),
        "payload": payload,
        "ts": time.time(),
    }


def emit_http(ev):
    req = urllib.request.Request(
        "http://127.0.0.1:%d/event" % port(),
        data=json.dumps(ev).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        r.read()
    return True


def emit_file(ev):
    d = os.path.join(os.getcwd(), ".devin", "rts")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "events.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {"hook_event_name": "unknown", "raw": "unparseable"}
    ev = event(payload)
    try:
        if not emit_http(ev):
            emit_file(ev)
    except Exception:
        try:
            emit_file(ev)
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
