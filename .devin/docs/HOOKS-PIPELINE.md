# Hooks pipeline

The aggregation contract for the consolidated hook entry points. Source
of truth for wiring: `hooks.v1.json` (ADR 005). Aggregation mechanics:
`scripts/_hookrun.py` (ADR 006). Event flow diagram:
`.devin/docs/diagrams/hook-event-flow.md`.

## Layers

1. **Event**: Devin CLI lifecycle event (`PreToolUse`, `PostToolUse`,
   `UserPromptSubmit`, `SessionStart`, `PostCompaction`, `Stop`,
   `SessionEnd`; `PermissionRequest` wired empty).
2. **Entry point**: one `command` per matcher in `hooks.v1.json`. Ten
   commands total, each `python scripts/<entry>.py`. Inner scripts are
   never bound directly.
3. **Inner scripts**: the entry point imports `_hookrun` and lists the
   check scripts to run in-process, in order.

## Entry points and inner scripts

| Entry point | Event / matcher | Inner scripts (order) |
|---|---|---|
| `pre-exec-guard.py` | PreToolUse `^exec$` | destructive-gate, architecture-gate, check-ai-signature, check-push-green, validate-tool-args, no-em-dash, laya-guard |
| `pre-write-guard.py` | PreToolUse `^(write\|edit\|notebook_edit)$` | ALWAYS: architecture-gate, validate-tool-args, no-em-dash; TEXT_ONLY (write/edit only): check-ai-signature, validate-mermaid |
| `post-exec.py` | PostToolUse `^(exec\|mcp_call_tool)$` | silent-error-review, context-pressure, compact-gate, memory-post-exec, gh-pr-assignee, stuck-detect |
| `memory-post-edit.py` | PostToolUse `^(write\|edit)$` | direct (no aggregator) |
| `compact-gate.py` | PostToolUse `^(write\|edit)$` | direct |
| `user-prompt.py` | UserPromptSubmit | constraint-pinning, behavioral-nudge, memory-retrieval, skill-picker, compact-gate |
| `session-start.py` | SessionStart | constraint-pinning, context-budget |
| `constraint-pinning.py` | PostCompaction | direct |
| `stop-guard.py` | Stop | check-ai-signature, refine-review-prompt, memory-stop, no-em-dash |
| `memory-stop.py` | SessionEnd | direct |

## Merge rules (`_hookrun.run`)

- Scripts run in the listed order, in one Python process (saves one
  interpreter spawn per inner script; ~50-80ms each).
- Any `decision: block` wins. The first blocker's full object is kept;
  exit code 2 propagates to the CLI.
- First non-block `decision` is used when nothing blocks.
- `hookSpecificOutput.additionalContext` strings concatenate in order,
  separated by a blank line.
- `hookSpecificOutput.updatedInput` objects shallow-merge (later keys
  overwrite earlier).
- Other `hookSpecificOutput` keys are set on first sight (setdefault).
- Non-JSON stdout lines are routed to stderr; hook stdout stays clean
  JSON for the CLI.
- A crashing inner script is fail-open: traceback to stderr, does not
  block, remaining scripts still run. No short-circuit on block either;
  all scripts run so context output is not lost.

## Exit-code mapping

- `0`: allow (no stdout, or stdout JSON with context only).
- `2`: block (`decision: block` in merged output).
- Inner `SystemExit(2)` marks the run blocked even if the script emitted
  no JSON.

## Timeout and failure boundaries

- The `timeout` in `hooks.v1.json` covers the whole entry point, so all
  inner scripts share one budget (300s pre-exec, 90s pre-write, 10-30s
  elsewhere). Per-script latency is invisible to the CLI timeout.
- `fail_closed: true` (both PreToolUse entries): if the entry point
  itself fails to run, the guarded tool call is blocked. Everywhere
  else, entry failure is fail-open.
- `PreCompact`/`PostCompact` are unwired by design: `PostCompaction` is
  the canonical pinning event; see TOOLS-MAP hook table notes.

## Inner-script contract

An inner script must: read one JSON payload from stdin; emit at most one
JSON object on stdout; exit 0/2; treat malformed input as allow; be
idempotent; and never be referenced directly in `hooks.v1.json`.
