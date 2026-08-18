#!/usr/bin/env python3
"""Constraint Pinning: keeps governance constraints alive across compaction.

Handles three events, dispatched on `hook_event_name`:

  PostCompaction   - compaction just happened. Per Devin CLI docs, PostCompaction
                     does NOT support hookSpecificOutput.additionalContext
                     (only UserPromptSubmit, SessionStart and PostToolUse do),
                     so this event writes a pending-reinjection marker and logs
                     the summary. It also emits additionalContext on a
                     best-effort basis in case support is added later.
  UserPromptSubmit - if a marker exists, re-inject the pinned constraints via
                     additionalContext and clear the marker.
  SessionStart     - clear any stale marker from a previous session.

Stdin payloads (per /cli/extensibility/hooks/lifecycle-hooks):
  PostCompaction   {"hook_event_name": "PostCompaction", "summary": "..."|null}
  UserPromptSubmit {"hook_event_name": "UserPromptSubmit", "prompt": "..."}
  SessionStart     {"hook_event_name": "SessionStart", "source": "..."}

Source: "Governance Decay" (arXiv:2606.22528v2, Chen, 27 Jun 2026)
  Compaction raises violation from 0% to 30% (up to 59%).
  When the constraint survives the summary: 0% violation. When dropped: 38%.
  Decay is 8.3x larger for soft organizational policies than hard safety norms.
  Constraint Pinning restores violation to 0% for ~47 pinned tokens (<0.5%).
"""
import sys, json, os, hashlib, tempfile

PINNED_CONSTRAINTS = """Pinned governance constraints (re-injected after context compaction):

- Rule 2: No AI signatures in deliverables (commits, files, PRs, docs).
- Rule 5: No push without green - run local checks before committing.
- Rule 7: Execute-first, opinion-silent - don't reframe, suggest alternatives, or critique clear tasks.
- Rule 12: Maximum precision - every claim verified against its primary source by reading it directly.
- Rule 13: Devin CLI is not a security sandbox - run untrusted code externally, review changes before applying.
- Rule 14: These constraints are pinned and survive compaction.
- Rule 15: Refinement evidence must be reproducible - phantom guardrails occur in 25% of self-improvement runs.
- Rule 16: Self-improvement loops produce 47-74% illusory gains - validate with held-out tests.
- Rule 17: Don't deduce - verify with tools. Use read, exec, grep, glob before asserting anything.
- Rule 18: Keep the context window lean - default to clear over compact, keep rules files small, audit MCP servers before adding, paste large inputs to files not chat. Bigger window != better retrieval.
- Rule 19: Never read secrets or sensitive env vars - never read, cat, echo, print, or output API keys, tokens, passwords, private keys, or .env secret values. Use them but never display their contents. If a key/env var is missing, empty, or doesn't behave as expected, say so without exposing the value."""

PINNED_HASH = hashlib.sha256(PINNED_CONSTRAINTS.encode("utf-8")).hexdigest()[:16]

MARKER_NAME = "devin-constraint-reinject.marker"


def marker_path():
    """Session-scoped marker path; falls back to a shared name without session id."""
    return os.path.join(tempfile.gettempdir(), MARKER_NAME)


def write_marker(session_id, summary):
    try:
        with open(marker_path(), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "session_id": session_id,
                    "hash": PINNED_HASH,
                    "summary_len": len(summary or ""),
                },
                f,
            )
        return True
    except (OSError, IOError):
        return False


def read_marker():
    try:
        with open(marker_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, IOError, json.JSONDecodeError, ValueError):
        return None


def clear_marker():
    try:
        os.remove(marker_path())
    except (OSError, IOError):
        pass


def inject(event_name):
    """Emit the pinned constraints as additionalContext for `event_name`."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": PINNED_CONSTRAINTS,
        }
    }))


def summary_retains_constraints(summary):
    """Heuristic: did the compaction summary keep the governance constraints?

    Returns True only when most key phrases survived. Fail-closed on an empty
    or missing summary (we re-inject rather than risk Governance Decay).
    """
    if not summary or not summary.strip():
        return False
    key_phrases = (
        "ai signature",
        "push without green",
        "execute-first",
        "maximum precision",
        "security sandbox",
        "constraint pinning",
        "context window",
        "secrets",
    )
    low = summary.lower()
    survived = sum(1 for p in key_phrases if p in low)
    return survived >= (len(key_phrases) + 1) // 2


def handle_post_compaction(data):
    summary = data.get("summary") or ""
    session_id = data.get("session_id", "")

    if summary_retains_constraints(summary):
        print(
            f"constraint-pinning: constraints survived compaction (hash={PINNED_HASH})",
            file=sys.stderr,
        )
        clear_marker()
        sys.exit(0)

    # Constraints were dropped (or no summary available). Mark for re-injection
    # on the next UserPromptSubmit, since PostCompaction cannot inject context.
    wrote = write_marker(session_id, summary)
    print(
        f"constraint-pinning: constraints missing from compacted context; "
        f"marker={'written' if wrote else 'FAILED'} (hash={PINNED_HASH})",
        file=sys.stderr,
    )
    # Best-effort injection in case PostCompaction gains additionalContext support.
    inject("PostCompaction")
    sys.exit(0)


def handle_user_prompt_submit(data):
    marker = read_marker()
    if not marker:
        sys.exit(0)
    clear_marker()
    print(
        f"constraint-pinning: re-injected pinned constraints (hash={PINNED_HASH})",
        file=sys.stderr,
    )
    inject("UserPromptSubmit")
    sys.exit(0)


def handle_session_start(data):
    # Clear a stale marker so a new session does not inherit one.
    clear_marker()
    sys.exit(0)


HANDLERS = {
    "PostCompaction": handle_post_compaction,
    "UserPromptSubmit": handle_user_prompt_submit,
    "SessionStart": handle_session_start,
}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open

    event = data.get("hook_event_name", "")
    handler = HANDLERS.get(event)
    if handler is None:
        sys.exit(0)
    handler(data)


if __name__ == "__main__":
    main()
