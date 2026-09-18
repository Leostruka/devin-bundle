# 14 — Held-out / validation test split

**Intent:** research proposed tests under tests/validation/ and
tests/held-out/; they landed in tests/ root. Held-out exists to catch
tuning-to-the-tests.

**What to build:** move cu workflow tests to `tests/validation/
test_cu_workflows.py`; create `tests/held-out/test_cu_workflows.py` with a
FIXED seed set declared before runs; document that held-out thresholds are
frozen before observation. Keep repo conftest compatibility.

**Proposed modules:** test files only.

**Estimated size (lines):** ~60 + moved tests

**Input / Output:** pytest paths -> green runs; frozen seed list

**Blocked by:** none

**Gate:** `python -m pytest tests/validation/test_cu_workflows.py tests/held-out/test_cu_workflows.py -q`

**Expect:** exit 0 both dirs; held-out seeds unchanged after first green run

**Evidence:** pytest output + seed list in file header

**Status:** resolved

- [ ] held-out seeds/thresholds frozen at creation
- [ ] validation suite remains the tuning surface

## Answer

Workflow tests moved to `tests/validation/test_cu_workflows.py`; frozen
held-out file `tests/held-out/test_cu_workflows.py` with seeds 101-105
declared pre-observation. Evidence: 18/18 green.
