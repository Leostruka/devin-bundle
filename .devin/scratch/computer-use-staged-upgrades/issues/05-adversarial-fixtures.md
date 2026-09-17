# 05 — Adversarial fixtures + workflow tests

**Intent:** catch stale-target/focus/Unicode races before they reach a real
desktop; every sequence seeded and replayable.

**What to build:** `tests/test_cu_workflows.py` (seeded end-to-end dry-run
chains: screenshot→hint→click/type with fakes; Unicode text plans; focus
change -> reject) and `tests/test_cu_stateful.py` (seeded action-sequence
generator over a fake desktop model asserting invariants: inputs always
released, stale hints never dispatch, sidecar generations monotonic).

**Proposed modules:** two test files only.

**Estimated size (lines):** ~200

**Input / Output:** pytest cases over fake modules

**Blocked by:** None — can start immediately (contracts already landed).

**Gate:** `python -m pytest tests/test_cu_workflows.py tests/test_cu_stateful.py -q`

**Expect:** exit 0; invariants hold across seeds 1..20

**Evidence:** pytest output

**Status:** resolved

- [ ] every run reproducible by seed
- [ ] zero dispatch on any stale/rejected path
- [ ] Unicode text plans handled without crashes

## Answer

`test_cu_workflows.py` (seeded observe->dispatch chains; expired/foreign/
focus-change -> zero dispatch; Unicode plans bounded) and
`test_cu_stateful.py` (20 seeds x 40 ops; no stuck inputs; replays
byte-identical). Evidence: 31/31.
