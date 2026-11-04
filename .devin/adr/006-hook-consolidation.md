# ADR 006: Hook consolidation into aggregator entry points

## Status

Accepted

## Context

The bundle originally bound ~21 hook commands individually in
`hooks.v1.json`: one process spawn per check, per matching tool call.
Each spawn pays ~50-80ms of Python interpreter startup while the actual
check takes under 10ms. On hot paths (every `exec`, every write) the
spawn cost dominated and multiplied linearly with the number of guards.

## Decision

`hooks.v1.json` binds 10 consolidated entry points (one per
event/matcher pair). Each entry point imports `scripts/_hookrun.py`,
which loads the inner check scripts as modules in a single process,
fakes their stdin/stdout, and merges their hook-protocol output. Merge
semantics: first `block` wins with exit 2; `additionalContext`
concatenates; `updatedInput` shallow-merges; a crashing inner script is
fail-open. Contract documented in `.devin/docs/HOOKS-PIPELINE.md`.

Invariant: inner scripts are never bound directly in `hooks.v1.json`.
Adding a check means appending it to an entry point's list, not adding a
matcher.

## Alternatives considered

- Broaden matchers and keep per-script commands: still pays one spawn
  per script per call; rejected on cost.
- One omnibus guard for all events: loses per-event timeouts, matcher
  precision, and the ability to fail_closed only PreToolUse; rejected on
  safety granularity.

## Consequences

- All inner scripts in one entry share the entry's timeout budget;
  per-script latency is invisible to the CLI timeout accounting.
- Inner scripts must satisfy the stdin/stdout contract in
  HOOKS-PIPELINE.md (one JSON payload in, at most one JSON object out,
  exit 0/2, malformed input = allow, idempotent).
- Failure semantics split cleanly: inner crash = fail-open via
  `_hookrun`; entry-point failure = `fail_closed` where the entry sets
  it (PreToolUse only).
- Measured savings: one interpreter spawn per event instead of 5-7; the
  spawn-cost rationale is inherent to interpreter startup (~50-80ms
  each), not separately benchmarked.
