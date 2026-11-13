# Task 11 brief — evidence-based native acceleration decision

## Plan reference

`.devin/plans/2026-09-19-system-control.md` Task 11 (~200-300 lines,
no Rust unless the decision gate passes — it almost certainly won't).

## Files

- Create `extensions/system-control/sc_bench.py`
- Create `tests/test_sc_bench.py`
- Create `.devin/research/system-control-benchmark.json` (measured
  baseline, ≥30 iterations per scenario)
- Conditional `.devin/adr/004-system-control-native-acceleration.md`
  — create ONLY if gate triggers; otherwise record
  `decision: "stay_python"` in the benchmark JSON.

## Contract (held-out pins — do NOT read held-out dir)

`sc_bench.run(fn, *, runs, warmup=0, clock=None, env=None)` returns
a JSON-serializable dict containing at least:

- `runs` (== measured iterations, warmup excluded),
- `p50_ms`, `p95_ms`, `max_ms` (non-negative, ordered
  max >= p95 >= p50),
- `env` when `env` arg passed (echo of `env_metadata()` output).

`sc_bench.env_metadata()` returns a dict of platform info that must
NOT contain usernames, absolute home paths, or secrets (no
"appdata", "\\users\\", local username, "secret", "token" in JSON).

Timing uses a monotonic clock (injectable `clock` callable).

## Scenarios to measure (Python baseline)

`process_snapshot`, `event_reduce`, `json_decode`, `stream_drain` —
use existing sc_* module paths (backends inventory, telemetry
reduce_events, contract JSON decode, session drain). ≥30 measured
iterations each after warmup; store summary + command + commit +
platform class in `.devin/research/system-control-benchmark.json`.

## Decision gate

Rust crate work is created ONLY when: baseline isolates a CPU/parser/
reducer hot path, the ADR records a predeclared latency budget, and
two independent runs reproduce the bottleneck. Otherwise record
`decision:"stay_python"` in the JSON and stop — this is the expected
outcome.

## TDD

1. `tests/test_sc_bench.py` FIRST (RED): fake clock, warmup
   exclusion, percentile ordering, env_metadata sanitization, JSON
   serializability, deterministic fixture scenario.
2. Implement `sc_bench.py` (stdlib only).
3. GREEN + run real baseline scenarios, write research JSON.
4. `python -m py_compile`.

## Out of scope

- Any Rust/cargo work unless gate passes (then ADR first).
- Changing sc_* module code to go faster — measure only.
