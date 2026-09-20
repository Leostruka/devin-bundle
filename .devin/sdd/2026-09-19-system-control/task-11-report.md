# Task 11 report — measured native-acceleration decision

## Scope

`sc_bench.py` (~125 lines) deterministic harness + real baseline +
recorded decision. No Rust — gate conditions unmet.

## Delivered

- `run(fn, *, runs, warmup=0, clock=None, env=None, scenario=None)` —
  `operator.index` runs/warmup (runs≥1, warmup≥0), warmup executed
  not recorded, monotonic injectable clock, JSON-serializable
  `{scenario, runs, warmup, min/p50/p95/max/mean_ms, env?}`.
- `env_metadata()` — platform/release/machine/python only; no
  usernames, home paths, secrets.
- `_main` CLI: `python extensions/system-control/sc_bench.py
  [--runs N] [--warmup N]` runs the four scenarios on real paths:
  `sc_backend.capabilities`, `sc_telemetry.reduce_events`
  (1000-event fixture), `sc_contract.validate_request`+`json.loads`,
  `open_stream/feed/drain/close_stream`.

## Baseline (Windows/AMD64, CPython 3.14.4, commit 7ec1bb4)

| scenario | p50_ms | p95_ms | max_ms |
|---|---|---|---|
| process_snapshot | 1.919 | 2.304 | 2.517 |
| event_reduce | 2.195 | 3.017 | 3.988 |
| json_decode | 0.003 | 0.003 | 0.003 |
| stream_drain | 0.096 | 0.102 | 0.149 |

50 measured iters + 10 warmup each. Reproduced independently:
p95s 2.31/2.34/0.003/0.107 — same distributions.

## Decision: `stay_python`

All p95 < 4 ms; no reproducible CPU/parser/reducer hot path; gate
conditions (hot path + predeclared budget + two reproductions)
unmet. No ADR-004, no crate. Evidence:
`.devin/research/system-control-benchmark.json`.

## Review

Independent review: Spec PASS / Standards PASS → minors fixed:
`operator.index` replaces silent `int()` coercion, `runs<1` guard,
argv `next(..., default)`, top-level pathlib import. Phantom
`run_bench.py` command reference corrected to the real invocation.

## Verification

- Held-out `test_bench_harness.py`: 5/5 pass.
- Focused: `test_sc_bench.py` 8 + held-out 5 → 13 passed.
- CLI smoke: `--runs 5` → 4 scenarios emitted.
