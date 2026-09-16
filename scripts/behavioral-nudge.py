#!/usr/bin/env python3
"""UserPromptSubmit hook: injects a behavioral self-check checklist.

Unlike mechanical hooks (validate-tool-args, destructive-gate), behavioral
rules (Rule 7 opinion-silent, Rule 8 telegraphic, Rule 4 skill discovery,
Rule 17 verify-with-tools) cannot be enforced by code — they require the
model to self-enforce. This hook increases compliance probability by
re-injecting a concise checklist before each response.

Stdin payload (per /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "UserPromptSubmit", "prompt": "...", "session_id": "..."}

Output: hookSpecificOutput.additionalContext with the checklist.
Exit code: 0 (always — this is a nudge, not a gate).
"""
import sys, json

NUDGE = """Self-check before responding (Rules 7, 8, 4, 17):

- Scope: exactly what was asked — no more, no less.
- Output: telegraphic, no filler or unsolicited opinions.
- Skills: matching skills invoked for non-trivial tasks.
- Verify: state observed with tools, not deduced."""

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": NUDGE,
        }
    }))
    sys.exit(0)

if __name__ == "__main__":
    main()
