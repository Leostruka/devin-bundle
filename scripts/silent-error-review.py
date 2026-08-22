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

Scope (ALTK, arXiv:2603.15473, ACM CAIS 2026):
  The ALTK Silent Error Review component is "best suited for tool responses
  that are verbose and/or based on tabular responses" (ALTK README). The hook
  matcher is therefore restricted to `^(exec|mcp_call_tool)$` — the tools that
  produce verbose/tabular output where silent errors actually hide. Empty
  reads, no-match searches, and short outputs are already visible to the agent
  and are NOT in ALTK's scope; flagging them is noise.

Problem citation (arXiv:2607.07405, KDD 2026 Workshop):
  "78% of observed failures are silent wrong-state failures with no tool
  error." This hook addresses the *detection* side of that finding. The
  paper's working *intervention* is pre-execution deterministic gates
  (implemented separately as `destructive-gate.py`); this hook is a
  complementary post-tool check, not a replication of the paper's mechanism.

Checks (only when success=true and tool is exec or mcp_call_tool):
  - error field is populated (silent failure)
  - output contains high-signal error indicators after noise removal

At most one finding is emitted per call to avoid multi-finding spam.
"""
import sys, json, re

# High-signal error indicators. Tightened to reduce false positives:
# - "error" requires a colon (avoids "error handling", "error recovery")
# - test-failure pattern requires a non-zero count (0 failures is noise)
ERROR_INDICATORS = (
    re.compile(r"\btraceback\b", re.IGNORECASE),
    re.compile(r"\bfatal(?:\s+error)?\b", re.IGNORECASE),
    re.compile(r"\bunhandled exception\b", re.IGNORECASE),
    re.compile(r"\bsegmentation fault\b", re.IGNORECASE),
    re.compile(r"\bcore dumped\b", re.IGNORECASE),
    re.compile(r"\bpanic:", re.IGNORECASE),
    re.compile(r"^\s*error\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\b(?:command not found|no such file or directory)\b", re.IGNORECASE),
    re.compile(r"\bpermission denied\b", re.IGNORECASE),
    re.compile(r"\b[1-9]\d*\s+(?:tests?\s+)?fail(?:ed|ures?)?\b", re.IGNORECASE),
    # Non-zero exit codes (exit code 1, Exit code 255, etc.)
    re.compile(r"\bexit\s+code\s+[1-9]\d*\b", re.IGNORECASE),
    re.compile(r"\bexited\s+with\s+(?:code\s+)?[1-9]\d*\b", re.IGNORECASE),
    # Common errno names that indicate real failures
    re.compile(r"\bEACCES\b|\bECONNREFUSED\b|\bECONNRESET\b|\bETIMEDOUT\b|\bENOENT\b"),
    # Python exception types (not just "exception" the word)
    re.compile(r"\b(?:ValueError|TypeError|KeyError|IndexError|AttributeError|RuntimeError|ImportError|ModuleNotFoundError|OSError|IOError|FileNotFoundError|NotImplementedError|ZeroDivisionError)\b"),
    # PowerShell error patterns
    re.compile(r"\b(?:ConvertFrom-Json|Invoke-WebRequest|Get-ChildItem)\b.*\berror\b", re.IGNORECASE),
    re.compile(r"^\s*ConvertFrom-Json\s*:\s*error", re.IGNORECASE | re.MULTILINE),
    # npm/cargo/go specific failure indicators
    re.compile(r"\bnpm\s+ERR!", re.IGNORECASE),
    re.compile(r"\bcargo(?::[a-z]+)*\s+(?:error|FAILED)\b", re.IGNORECASE),
    re.compile(r"\bBUILD\s+FAILED\b", re.IGNORECASE),
    re.compile(r"\bFAIL\s+(?:github\.com|./)", re.IGNORECASE),
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
    re.compile(r"\b0\s+(?:tests?\s+)?fail(?:ed|ures?)?\b", re.IGNORECASE),
    re.compile(r"\berrors?\s*[:=]\s*0\b", re.IGNORECASE),
)


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
    """Emit at most one finding as additionalContext so the agent sees it."""
    if not findings:
        sys.exit(0)
    body = "Silent-error review flagged this tool result:\n- " + findings[0]
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

    emit(findings)


if __name__ == "__main__":
    main()
