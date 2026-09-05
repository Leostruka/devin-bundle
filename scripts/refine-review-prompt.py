#!/usr/bin/env python3
"""Stop hook: prompts refinement review after complex sessions.

Stdin payload (per /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "Stop", "stop_hook_active": false}

Stop does not support hookSpecificOutput.additionalContext, but it does support
a top-level {"decision": "block", "reason": ...}. This hook blocks the stop
exactly once per marker so the reminder reaches the agent, then deletes the
marker so the next stop succeeds. That avoids the documented stop-hook loop
risk while still surfacing the reminder.

Exit codes (per /cli/extensibility/hooks/overview#exit-codes):
  0 = allow stop, 2 = block stop (re-prompts the agent).

If `stop_hook_active` is already true, the hook exits immediately - another stop
hook is mid-flight and blocking again risks a loop.

Evidence: instruction compliance decays 5.6% per generation step
(arXiv:2605.10039). Lessons extracted before session end persist; lessons lost
on exit are gone.
"""
import sys, json, os, re


STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "and", "or",
    "but", "not", "no", "yes", "do", "did", "does", "it", "this", "that",
    "if", "else", "return", "def", "pass", "import", "from",
})


def devin_home():
    """Return the Devin user config home.

    Windows: %APPDATA%\\devin
    Unix: $XDG_CONFIG_HOME/devin or ~/.config/devin
    """
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


MARKER_NAME = ".refine-pending"

REMINDER = (
    "Session was marked as complex ({detail}).\n"
    "Before stopping, run the `primeagent-reference` skill in Refine mode:\n"
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
        os.path.join(devin_home(), MARKER_NAME),
    ]
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
    sys.exit(2)


# --- Bidirectional patch verification ---


def reconstruct_problem_from_patch(patch_text):
    """Blind backward reconstruction: infer the problem from a diff alone.

    Does not see the original issue. Returns a dict with affected paths,
    detected intent, and a reconstructed problem phrase.
    """
    if not patch_text:
        return {
            "affected_paths": [],
            "intent_terms": [],
            "reconstructed_problem": "no patch provided",
        }
    paths = set()
    terms = set()
    for line in patch_text.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            parts = line.split(None, 2)
            if len(parts) >= 2:
                path = parts[1]
                if path != "/dev/null":
                    paths.add(path)
                    # Extract filename stem as an intent term.
                    filename = os.path.basename(path)
                    stem = os.path.splitext(filename)[0]
                    if stem and stem not in ("a", "b"):
                        terms.add(stem)
        if line.startswith("+") and not line.startswith("+++"):
            # Look for keyword hints and meaningful words in added lines.
            lowered = line.lower()
            for keyword in ("fix", "bug", "error", "handle", "validate", "guard", "reject", "accept"):
                if keyword in lowered:
                    terms.add(keyword)
            for token in re.findall(r"\b[a-z]{3,}\b", lowered):
                if token in STOPWORDS:
                    continue
                terms.add(token)
    return {
        "affected_paths": sorted(paths),
        "intent_terms": sorted(terms),
        "reconstructed_problem": " ".join(sorted(terms)),
    }


def compare_problems(requested, reconstructed):
    """Return overlap metrics between requested and reconstructed problem strings."""
    requested_tokens = set(re.findall(r"\b\w+\b", requested.lower()))
    reconstructed_tokens = set(re.findall(r"\b\w+\b", reconstructed.lower()))
    if not requested_tokens:
        return {"overlap": 0.0, "missing": [], "extra": sorted(reconstructed_tokens)}
    intersection = requested_tokens & reconstructed_tokens
    overlap = len(intersection) / len(requested_tokens)
    missing = sorted(requested_tokens - reconstructed_tokens)
    extra = sorted(reconstructed_tokens - requested_tokens)
    return {"overlap": overlap, "missing": missing, "extra": extra}


def verify_patch_alignment(requested_problem, patch_text, symptom_only_terms=None, min_overlap=0.3):
    """Reconcile the requested problem with the patch's blind reconstruction.

    Verdict:
      aligned  — reconstruction covers enough of the requested problem.
      symptom_only — patch only touches surface terms, missing root cause.
      unrelated — reconstruction does not match the requested problem.
    """
    symptom_only_terms = set(t.lower() for t in (symptom_only_terms or []))
    recon = reconstruct_problem_from_patch(patch_text)
    metrics = compare_problems(requested_problem, recon["reconstructed_problem"])
    overlap = metrics["overlap"]
    missing_root = any(t in symptom_only_terms for t in metrics["missing"])

    if overlap < 0.05:
        return {
            "verdict": "unrelated",
            "reason": "patch reconstruction does not match the requested problem",
            "overlap": overlap,
            "reconstruction": recon,
            "metrics": metrics,
            "revision_guidance": "revise patch to address: " + ", ".join(metrics["missing"][:10]),
        }
    if overlap < min_overlap or missing_root:
        return {
            "verdict": "symptom_only",
            "reason": "patch addresses visible terms but misses root-cause concepts",
            "overlap": overlap,
            "reconstruction": recon,
            "metrics": metrics,
            "revision_guidance": "include root-cause work for: " + ", ".join(metrics["missing"][:10]),
        }
    return {
        "verdict": "aligned",
        "reason": "patch reconstruction matches the requested problem",
        "overlap": overlap,
        "reconstruction": recon,
        "metrics": metrics,
    }


if __name__ == "__main__":
    main()
