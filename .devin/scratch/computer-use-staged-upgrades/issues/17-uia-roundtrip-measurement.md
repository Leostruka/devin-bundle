# 17 — UIA round-trip measurement vs baseline

**Intent:** §6.2-etapa-3 requires comparing property round-trips with a
baseline for the same query — never measured.

**What to build:** counter instrumentation in fake UIA provider (count
property fetches) + real measurement via cu_bench hints_enum with and
without FindAllBuildCache; record numbers in cu-stage-report.md.

**Proposed modules:** test instrumentation + bench flag `CU_HINT_NOCACHE=1`
in cu_hints for A/B.

**Estimated size (lines):** ~70 + ~50 tests

**Input / Output:** cached vs uncached enum -> round-trip counts + ms

**Blocked by:** none

**Gate:** `python -m pytest tests/test_cu_uia_actions.py -q` + bench A/B
recorded

**Expect:** counts + timings written to report; uncached path available for
comparison only

**Evidence:** bench JSON + report section

**Status:** resolved

- [ ] round-trip count asserted in fake-provider test
- [ ] A/B numbers recorded, not asserted directional

## Answer

`CU_HINT_NOCACHE=1` bypass flag landed; fake-provider test asserts cached=0
live reads vs uncached=5/element. Real A/B: 29.8ms vs 34.4ms p50 (~15%).
Recorded in cu-stage-report.md. Evidence: 8/8 + bench numbers.
