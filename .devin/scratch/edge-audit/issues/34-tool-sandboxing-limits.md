# 34 -- Per-skill/agent tool sandboxing limited to validate-tool-args plus allowed-tools frontmatter

- **Status**: open
- **Category**: devin-cli-limitations
- **Severity**: P2
- **File**: scripts/validate-tool-args.py:1-55

## Evidence

The CLI offers no per-skill tool sandbox; the bundle layers two partial controls: `allowed-tools` frontmatter per agent profile (grants only, flat list) and `validate-tool-args.py`, a PreToolUse hook that validates argument shape for 19/28 tools but cannot scope rules per skill or per agent (hook payload has tool_name/tool_input/session_id, no invoking-skill identity). Command-content gating (rm -rf, force-push, pipe-to-shell) lives in `pre-exec-guard.py`/`destructive-gate.py`; `permissions.deny` in config covers only Write/Read path globs for secrets (COMPATIBILITY.md:184-192).

## Recommendation

Use `session_id`-keyed state: when `run_subagent` fires, record the dispatched profile for the session, then let `pre-exec-guard.py`/`validate-tool-args.py` apply per-profile deny rules (e.g. researcher may not exec). Alternatively adopt `permissions` `ask`/`deny` rules for Exec patterns now that `Exec(*)` matching exists (3000.10.31).

## Tradeoffs

- Merits of current workaround: argument validation catches hallucinated paths/regexes before they become real errors; flat allowed-tools is simple and CLI-native; destructive gate covers the highest-risk exec patterns.
- Demerits: a read-only profile that gains exec via prompt injection or frontmatter drift is gated only by the flat list, not by runtime intent; hook state keyed on session_id adds cross-hook coupling and a new failure mode (stale state); `Exec(*)` deny rules are blunt (deny beats allow, no per-profile scoping either).
- Better contorno: `--sandbox` (OS-level, writable roots + network filter) is the real isolation boundary but requires WSL 2 on Windows; it complements rather than replaces arg validation.

## Verification

`grep -n 'profile\|agent' scripts/validate-tool-args.py` shows no per-profile policy table; TOOLS-MAP.md documents 9 tools excluded from validation as "trivial".
