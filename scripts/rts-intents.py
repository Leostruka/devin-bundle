#!/usr/bin/env python3
"""rts-intents - UserPromptSubmit hook surfacing pending RTS overlay intents.

Stdin payload: Devin CLI hook JSON (hook_event_name, session_id, ...).

Reads <cwd>/.devin/rts/intents/*.json written by the RTS UI (via rtsd
POST /intent). For each status=="pending" intent:
  - kind "message": deposits the text into .devin/mailboxes/<to>/inbox/
    msg-<ts>.json (primeagent-reference mailbox format), marks delivered.
  - kinds spawn/goal/answer: announced to the agent via additionalContext;
    the orchestrator (leo/project-orchestrator) decides whether to act.
    Marked "surfaced" so they are announced exactly once.

Output: {"hookSpecificOutput": {"hookEventName":"UserPromptSubmit",
"additionalContext": "..."}} when pending/surfaced intents exist; otherwise
prints nothing.

Exit codes: always 0 (fail-open).
"""
import json
import os
import re
import sys
import time

SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def intents_dir():
    return os.path.join(os.getcwd(), ".devin", "rts", "intents")


def mailbox_deposit(to, text, sender="rts-ui"):
    if not SAFE_NAME.match(to or "") or ".." in to or not to.lstrip("."):
        raise ValueError("unsafe mailbox name")
    d = os.path.join(os.getcwd(), ".devin", "mailboxes", to, "inbox")
    os.makedirs(d, exist_ok=True)
    mid = "msg-%d" % int(time.time() * 1000)
    msg = {"id": mid, "from": sender, "to": to,
           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "type": "task", "content": text, "status": "unread"}
    with open(os.path.join(d, mid + ".json"), "w", encoding="utf-8") as f:
        json.dump(msg, f, ensure_ascii=False, indent=2)


def main():
    try:
        idir = intents_dir()
        if not os.path.isdir(idir):
            return
        lines = []
        for fn in sorted(os.listdir(idir)):
            if not fn.endswith(".json"):
                continue
            p = os.path.join(idir, fn)
            try:
                it = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            if it.get("status") != "pending":
                continue
            kind = it.get("kind")
            if kind == "message":
                try:
                    mailbox_deposit(it.get("to", "parent"),
                                    it.get("text", ""))
                    it["status"] = "delivered"
                    lines.append("- msg -> @%s: %s" % (it.get("to"),
                                                       it.get("text")))
                except Exception:
                    it["status"] = "rejected"
                    lines.append("- msg REJECTED (unsafe target): %s"
                                 % it.get("to"))
            else:
                it["status"] = "surfaced"
                if kind == "spawn":
                    lines.append("- spawn hero: profile=%s task=%s"
                                 % (it.get("profile"), it.get("task", "")[:80]))
                elif kind == "goal":
                    lines.append("- new goal: %s" % it.get("text", "")[:120])
                else:
                    lines.append("- %s: %s" % (kind, json.dumps(it)[:100]))
            try:
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(it, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        if lines:
            ctx = ("RTS overlay: %d intent(s) from the UI (route via "
                   "orchestrator skills; do not auto-execute):\n" % len(lines)
                   + "\n".join(lines))
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ctx}}))
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
