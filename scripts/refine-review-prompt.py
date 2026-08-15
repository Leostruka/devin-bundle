#!/usr/bin/env python3
"""Stop hook: prompts refinement review after complex sessions.

Stdin payload (per /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "Stop", "stop_hook_active": false}

Stop does not support hookSpecificOutput.additionalContext, but it does support
a top-level {"decision": "block", "reason": ...}. This hook blocks the stop
exactly once per marker so the reminder reaches the agent, then deletes the
marker so the next stop succeeds. That avoids the documented stop-hook loop
risk while still surfacing the reminder.

If `stop_hook_active` is already true, the hook exits immediately - another stop
hook is mid-flight and blocking again risks a loop.

Evidence: instruction compliance decays 5.6% per generation step
(arXiv:2605.10039). Lessons extracted before session end persist; lessons lost
on exit are gone.
"""
import sys, json, os

MARKER_NAME = ".refine-pending"

REMINDER = (
    "Session was marked as complex ({detail}).\n"
    "Before stopping, run the `refine` skill:\n"
    "- Review the trajectory for recurring failures, reusable tactics, and "
    "hard-won knowledge.\n"
    "- Refinement evidence must include a reproducible command (AGENTS.md Rule 15); "
    "vague evidence is a phantom guardrail.\n"
    "- Log each refinement to .devin/refinements.log.jsonl.\n"
    "The pending marker has been cleared, so stopping again will succeed."
)


def marker_paths():
    project_dir = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    paths = [
        os.path.join(project_dir, ".devin", MARKER_NAME),
        os.path.join(os.path.expanduser("~"), ".config", "devin", MARKER_NAME),
    ]
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        paths.append(os.path.join(appdata, "devin", MARKER_NAME))
    return paths


def find_marker():
    """Return (path, detail) for the first existing marker, else (None, None)."""
    for path in marker_paths():
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return path, f.read().strip()
            except (OSError, IOError):
                return path, ""
    return None, None


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open

    if data.get("hook_event_name", "") != "Stop":
        sys.exit(0)

    # Never block when another stop hook is already active (loop protection).
    if data.get("stop_hook_active"):
        sys.exit(0)

    path, detail = find_marker()
    if not path:
        sys.exit(0)

    # Consume the marker first so this can only block once.
    try:
        os.remove(path)
    except (OSError, IOError):
        # Cannot clear the marker; do not block or the agent could loop.
        print(
            f"refine-review-prompt: could not remove marker {path}; skipping block.",
            file=sys.stderr,
        )
        sys.exit(0)

    print(json.dumps({
        "decision": "block",
        "reason": REMINDER.format(detail=detail or "3+ todos completed"),
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
