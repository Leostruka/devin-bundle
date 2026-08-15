#!/usr/bin/env python3
"""PostToolUse hook: detects silent semantic errors in tool responses.

Stdin payload (per Devin CLI docs /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "PostToolUse", "tool_name": "exec",
   "tool_input": {...},
   "tool_response": {"success": true, "output": "...", "error": null},
   "session_id": "...", "prompt_id": "..."}

Never blocks. Emits findings via hookSpecificOutput.additionalContext, which
PostToolUse supports (per /cli/extensibility/hooks/overview#output-format), so
the agent actually sees the warning instead of it being lost on stderr.

Checks:
  - success=true but output contains error indicators (silent failure)
  - success=true but error field is populated
  - read/webfetch: empty output
  - grep/glob: empty output despite a plausible pattern

Source: ALTK Silent Error Review (arXiv:2603.15473, ACM CAIS 2026)
  Detects subtle semantic errors in tool responses that agents miss.
  "78% of observed failures are silent wrong-state failures with no tool error"
  (arXiv:2607.07405, KDD 2026 Workshop).
"""
import sys, json, re

# High-signal error indicators
ERROR_INDICATORS = (
    re.compile(r"\btraceback\b", re.IGNORECASE),
    re.compile(r"\bfatal(?:\s+error)?\b", re.IGNORECASE),
    re.compile(r"\bunhandled exception\b", re.IGNORECASE),
    re.compile(r"\bsegmentation fault\b", re.IGNORECASE),
    re.compile(r"\bcore dumped\b", re.IGNORECASE),
    re.compile(r"\bpanic:", re.IGNORECASE),
    re.compile(r"^\s*error[:\s]", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\b(?:command not found|no such file or directory)\b", re.IGNORECASE),
    re.compile(r"\bpermission denied\b", re.IGNORECASE),
    re.compile(r"\b\d+ (?:tests? )?fail(?:ed|ures?)\b", re.IGNORECASE),
)

# Lines to ignore (routine warnings, not failures)
NOISE_PATTERNS = (
    re.compile(r"deprecat", re.IGNORECASE),
    re.compile(r"\bnpm warn\b", re.IGNORECASE),
    re.compile(r"\bpip warn\b", re.IGNORECASE),
    re.compile(r"\bwarning\b", re.IGNORECASE),
    re.compile(r"\bnotice\b", re.IGNORECASE),
    re.compile(r"\bhint:", re.IGNORECASE),
    re.compile(r"\badvice\b", re.IGNORECASE),
    re.compile(r"\b0 (?:tests? )?fail(?:ed|ures?)\b", re.IGNORECASE),
    re.compile(r"\berrors?\s*[:=]\s*0\b", re.IGNORECASE),
)

# Tools whose empty output is meaningful
EMPTY_OUTPUT_TOOLS = {"read", "webfetch", "notebook_read"}
SEARCH_TOOLS = {"grep", "glob", "find_file_by_name"}


def signal_lines(text):
    """Strip routine-noise lines, returning the remaining signal."""
    kept = [ln for ln in text.split("\n") if not any(n.search(ln) for n in NOISE_PATTERNS)]
    return "\n".join(kept).strip()


def has_real_error(text):
    """True when text contains a genuine error indicator after noise removal."""
    if not text or not text.strip():
        return False
    signal = signal_lines(text)
    if not signal:
        return False
    return any(p.search(signal) for p in ERROR_INDICATORS)


def emit(findings):
    """Emit findings as additionalContext so the agent sees them."""
    if not findings:
        sys.exit(0)
    body = "Silent-error review flagged this tool result:\n" + "\n".join(
        f"- {f}" for f in findings
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": body,
        }
    }))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open

    tool_name = data.get("tool_name", "") or ""
    tool_input = data.get("tool_input") or {}
    response = data.get("tool_response") or {}

    if not isinstance(response, dict):
        sys.exit(0)

    success = response.get("success", True)
    output = response.get("output") or ""
    error = response.get("error") or ""
    if not isinstance(output, str):
        output = str(output)
    if not isinstance(error, str):
        error = str(error)

    findings = []

    # A reported failure is already visible to the agent; only silent ones matter.
    if success:
        if error.strip():
            findings.append(
                f"{tool_name} reported success but populated the error field: "
                f"{error.strip()[:200]}"
            )
        elif has_real_error(output):
            snippet = signal_lines(output)[:200]
            findings.append(
                f"{tool_name} reported success but the output contains error "
                f"indicators: {snippet}"
            )

        if tool_name in EMPTY_OUTPUT_TOOLS and output.strip() == "":
            target = (
                tool_input.get("file_path")
                or tool_input.get("url")
                or tool_input.get("notebook_path")
                or "the target"
            )
            findings.append(
                f"{tool_name} returned empty content for {target}. "
                "The resource may be empty, unreadable, or the wrong path."
            )

        if tool_name in SEARCH_TOOLS and output.strip() == "":
            pattern = tool_input.get("pattern", "")
            if isinstance(pattern, str) and len(pattern) > 2:
                findings.append(
                    f"{tool_name} returned no matches for pattern '{pattern}'. "
                    "Verify the pattern and the search path before concluding the "
                    "target does not contain it."
                )

    emit(findings)


if __name__ == "__main__":
    main()
