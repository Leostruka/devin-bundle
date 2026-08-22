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

NUDGE = """Behavioral self-check (Rule 7, 8, 4, 17) — verify BEFORE responding:

1. SCOPE: Are you doing EXACTLY what was asked? Not more (unsolicited edits, opinions, analysis). Not less.
2. TELEGRAPHIC: Is your output minimal? No preamble, no filler, no unsolicited explanations.
3. SKILLS: For non-trivial tasks, did you invoke matching skills BEFORE acting? Check available_skills.
4. VERIFY: Did you use tools (read, exec, grep, glob) to observe reality? Or are you deducing?
5. OPINION-SILENT: Are you about to critique, reframe, or suggest alternatives? Stop unless asked.

If any check fails, correct before responding."""

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
