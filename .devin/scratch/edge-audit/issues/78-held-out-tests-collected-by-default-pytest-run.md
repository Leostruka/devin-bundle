# 78 -- held-out and validation tests are collected by the default pytest run
- **Status**: open
- **Category**: test-coverage
- **Severity**: P2
- **File**: pytest.ini:1-7
## Evidence
`pytest.ini` sets `testpaths = tests` with no `norecursedirs`, `-m` filter, or `collect_ignore`. `tests/held-out/` and `tests/validation/` sit under `tests/` and contain `test_*.py` files (e.g. `tests/held-out/test_cu_env_boundaries.py`, `tests/validation/test_akita_gapfill_contract.py`); `tests/held-out/conftest.py` only fixes imports, it does not deselect. So a bare `python -m pytest` runs the held-out suite together with everything else. Global rules (Rule 15) require held-out tests to stay held out from the agent's normal validation loop; running them every time erodes that and also means `check-push-green.py` (which runs plain `pytest`, scripts/check-push-green.py:87) gates pushes on held-out results it was not meant to consult.
## Recommendation
Exclude held-out from default collection: add `norecursedirs = tests/held-out` (and validation if intended separate) to pytest.ini, plus an explicit `--rootdir`-scoped invocation or a `-m heldout` marker + separate documented command (`pytest tests/held-out -p no:cacheprovider`) for the refine loop.
## Tradeoffs
Validation tests may be intended to run always; only held-out is clearly mis-scoped. Split config or markers, not a second ini file, keeps one suite entry point.
## Verification
Run `python -m pytest --collect-only -q` and confirm `tests/held-out/` items appear in the collected list.

## Answer
`pytest.ini` gained `norecursedirs = held-out`. Bare `python -m pytest` (and `pytest tests/`) collects 0 held-out items while `pytest tests/held-out -q` still collects 212, matching how check-push-green.py invokes the held-out suite explicitly. Validation tests remain in the default run.

Status: resolved
