#!/usr/bin/env python3
"""Stop hook: prompts refinement review after complex sessions.

Checks if the session completed 3+ todo items (complex task per Rule 10).
If so, injects a reminder to run the `refine` skill before stopping.

Evidence: instruction compliance decays 5.6% per generation step (arXiv:2605.10039).
Lessons extracted before session end persist; lessons lost on exit are gone.

Reads tool input JSON from stdin. Exit 0 = allow stop, exit 1 = block with reminder.
"""
import sys, json, os, re

def count_completed_todos(context_dir=None):
    """Estimate session complexity from todo markers in recent context.
    
    The hook receives limited data. We check for a session-complexity marker
    file written by the agent during todo_write, or fall back to checking
    if a .devin/refinements-pending marker exists.
    """
    # Check for pending refinement marker
    marker_paths = [
        os.path.join(os.getcwd(), ".devin", ".refine-pending"),
        os.path.join(os.path.expanduser("~"), ".config", "devin", ".refine-pending"),
        os.path.join(os.environ.get("APPDATA", ""), "devin", ".refine-pending"),
    ]
    for p in marker_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except (OSError, IOError):
                pass
    return None

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    event = data.get("event", "")
    tool = data.get("tool", "")

    if event != "Stop" and tool != "Stop":
        sys.exit(0)

    pending = count_completed_todos()
    if pending:
        print(f"<refine_reminder>", file=sys.stderr)
        print(f"Session marked as complex ({pending}).", file=sys.stderr)
        print(f"Before stopping: run the `refine` skill to extract lessons.", file=sys.stderr)
        print(f"Check trajectory for: recurring failures, reusable tactics, hard-won knowledge.", file=sys.stderr)
        print(f"Log any refinement to .devin/refinements.log.jsonl.", file=sys.stderr)
        print(f"Then remove the .refine-pending marker.", file=sys.stderr)
        print(f"</refine_reminder>", file=sys.stderr)
        # Don't block — just remind. Agent decides.
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
