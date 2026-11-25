# Hooks pipeline

The aggregation contract for the consolidated hook entry points. Source
of truth for wiring: `hooks.v1.json` (ADR 005). Aggregation mechanics:
`scripts/_hookrun.py` (ADR 006). Event flow diagram:
`.devin/docs/diagrams/hook-event-flow.md`.

## Layers

1. **Event**: Devin CLI lifecycle event (`PreToolUse`, `PostToolUse`,
   `UserPromptSubmit`, `SessionStart`, `PostCompaction`, `Stop`,
   `SessionEnd`; `PermissionRequest` approve-only).
2. **Entry point**: `command`s per matcher in `hooks.v1.json`. Fourteen
   commands total (six consolidated `_hookrun` entry points plus eight
   direct single-script commands; the write/edit PostToolUse matcher
   carries four direct commands). Inner scripts are never bound directly
   under consolidated entry points.
3. **Inner scripts**: the entry point imports `_hookrun` and lists the
   check scripts to run in-process, in order.

## Entry points and inner scripts

| Entry point | Event / matcher | Inner scripts (order) |
|---|---|---|
| `pre-exec-guard.py` | PreToolUse `^(exec\|write_to_process)$` | destructive-gate, architecture-gate, check-ai-signature, check-push-green, validate-tool-args, no-em-dash, laya-guard |
| `pre-write-guard.py` | PreToolUse `^(write\|edit\|notebook_edit)$` | ALWAYS: architecture-gate, validate-tool-args, no-em-dash; TEXT_ONLY (write/edit only): check-ai-signature, validate-mermaid |
| `post-exec-guard.py` | PostToolUse `^(exec\|write_to_process\|mcp_call_tool)$` | routes by tool: exec -> dep-audit-gate + post-exec; write_to_process -> dep-audit-gate; mcp_call_tool -> post-exec |
| `post-write-guard.py` | PostToolUse `^(write\|edit)$` | memory-post-edit, compact-gate, file-size-guard, design-lint-gate |
| `user-prompt.py` | UserPromptSubmit | constraint-pinning, behavioral-nudge, memory-retrieval, skill-picker, compact-gate, token-saver |
| `validate-tool-args.py` | PreToolUse `^(run_subagent\|mcp_call_tool\|mcp_read_resource\|webfetch\|web_search\|skill\|request_scope\|ask_user_question\|todo_write\|browser_preview)$` | direct |
| `session-start.py` | SessionStart | constraint-pinning, context-budget, hook-drift |
| `constraint-pinning.py` | PostCompaction | direct |
| `context-pressure.py` | PostCompaction | direct (resets pressure marker; also inner of post-exec) |
| `compact-gate.py` | PostCompaction | direct (resets gate state; also inner of post-write-guard/post-exec/user-prompt) |
| `stop-guard.py` | Stop | check-ai-signature, refine-review-prompt, memory-stop, no-em-dash, rl-resume-detect, decision-queue |
| `memory-stop.py` | SessionEnd | direct |
| `permission-gate.py` | PermissionRequest `^exec$` | direct (approve-only; silent = human decides) |

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
- Non-JSON stdout lines are dropped (shown only with
  `DEVIN_HOOKRUN_DEBUG`); hook stdout stays clean JSON for the CLI.
- **Child stderr is dropped** (the CLI treats hook stderr as a failure
  under `fail_closed`). Warn/advisory output from an inner script MUST go
  through `hookSpecificOutput.additionalContext` on stdout; printing to
  stderr too is fine, but stderr alone reaches nobody (C80).
- **`hookSpecificOutput` requires `hookEventName`**: an emission without
  it fails CLI parsing, the whole hook call "fails", and `fail_closed`
  blocks the tool call with an opaque error (C84). `_hookrun`
  synthesizes the field from the payload as a backstop.
- A crashing inner script is fail-open: traceback to stderr, does not
  block, remaining scripts still run. No short-circuit on block either;
  all scripts run so context output is not lost.
- **write_to_process normalization**: `run()` injects the CR/LF-submitted
  stdin lines as `tool_input.command` before dispatch, so every inner
  gate sees the real commands (C90-C93). Pending input-line text is
  buffered per `session|event|shell` under `state/wtp-*.txt` (phase-keyed
  so pre/post hooks model the same stream independently; C-c/C-u/C-g
  clear). Buffers are JSON `{p, i, o}` records: `i` (input hash) makes
  extraction idempotent so downstream gates always re-extract - a
  caller-supplied `command` or trust flag on wtp is never trusted
  (C98). Line-edit/recall controls map to a `\x1e` sentinel; a submit
  carrying it blocks (C94/C96/C97). File buffers are enforcement state -
  the state-file guards cover them (incl. the `cd state &&` arm, C97).

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

## CLI payload contract (fields the pipeline depends on)

The runtime trusts these inbound fields; if the CLI stops sending them
the corresponding enforcement silently degrades:

- `hook_event_name`: drives event-scoped arms and the synthesized
  `hookEventName` on merged `hookSpecificOutput`. When absent, each
  consolidated entry point falls back to its statically registered event
  (`_hookrun.main(..., event=...)` / `run(..., event=...)`; C13/C123).
- `agent_id` / `subagent_id` / `is_subagent`: `_enforce_profile_deny`
  (validate-tool-args.py) only fires when the payload carries one of
  these markers. If the CLI ever drops them, every profile deny no-ops.
  Pinned by fixture tests; mixed-profile sessions fail open by design
  (uniform-deny) because the CLI does not send a reliable per-agent id.
- `session_id`: keys wtp buffers, gate state, and the context-pressure
  marker. Absent -> per-call state collapses to stateless behavior.
- `tool_name` / `tool_input`: matcher and gate scan surface. The wtp
  channel synthesizes `tool_input.command` from raw stdin lines before
  dispatch so gates always see real commands.
