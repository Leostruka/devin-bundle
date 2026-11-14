# 15 — Missing adversarial cases

**Intent:** cover the remaining §6.2-etapa-8 case list: modais, resize/DPI,
virtualized lists, provider failure mid-sequence, potential duplicate
submission.

**What to build:** extend stateful generator + workflow fixtures: modal
blocks pointer target (action must route/reject, not click through); DPI
scale change between observe and dispatch -> stale geometry rejected;
virtualized list element disappears between enum and action; provider
raises mid-enum -> typed failure; dispatch result 'unknown' never auto-
retries the same action.

**Proposed modules:** `tests/test_cu_stateful.py`,
`tests/test_cu_workflows.py` (+fake DPI/monitor change fixture).

**Estimated size (lines):** ~150 tests

**Input / Output:** pytest cases over fakes

**Blocked by:** 14

**Gate:** `python -m pytest tests/test_cu_stateful.py tests/test_cu_workflows.py -q`

**Expect:** exit 0; every case has a typed outcome (reject/timeout/fallback),
never silent wrong-target dispatch

**Evidence:** pytest output

**Status:** resolved

- [ ] geometry change invalidates hints
- [ ] duplicate-submission path never re-fires
- [ ] provider failure mid-enum -> typed error

## Answer

Real gap found: resolve_hint had no generation check — cross-observation hint
ids resolved silently. Added `generation` param (stale_generation rejection) +
`--gen` flag on mouse/type_text so callers can pin the observation they saw.
New cases: stale-generation re-observe, disabled-element semantic gate.
Evidence: validation 10/10.
