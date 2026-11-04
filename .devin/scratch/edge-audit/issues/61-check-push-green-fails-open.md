# 61 -- check-push-green fails open on timeout, error, and missing framework

- **Status**: resolved
- **Category**: applied-rules
- **Severity**: P1
- **File**: scripts/check-push-green.py:60-71, 177

## Evidence

`run_check` returns `(True, "...allowing push")` on `TimeoutExpired` (line 67)
and on `FileNotFoundError`/`OSError` (line 71). `MAIN_TIMEOUT` is 45s (line 34)
while `TEST_TIMEOUT` is 120s (line 30): on this repo `python -m pytest` collects
100+ test files and regularly exceeds 45s, so the primary Rule 5 gate degrades
to a no-op under exactly the conditions it exists for. `main()` also exits 0
when `detect_test_command` finds no marker (line 177). Every failure path in
the gate resolves to "allow".

## Recommendation

Treat timeout as failure for the main suite (or run `pytest --lf -x -q` which
fits the budget), and emit a warning block when no framework is detected in a
project that has a tests/ directory. At minimum, log that the gate was skipped
so pushes are auditable.

## Tradeoffs

Failing closed on timeout can block pushes on machines where pytest is
genuinely slow; a scoped `--lf` rerun keeps the gate meaningful without the
full-suite cost.

## Verification

Run `python -c "print(open('scripts/check-push-green.py').read()[1800:2600])"`
or time `python -m pytest --collect-only -q`; confirm it exceeds 45s, then
confirm the hook would still allow `git push`.

## Answer
Fail-closed implemented: `run_check` now returns a status
("pass"/"fail"/"timeout"/"unavailable") and the main gate blocks on anything
but "pass", so a timed-out or unrunnable suite can no longer degrade the
gate to a no-op. The no-framework path now distinguishes the two cases: a
`tests/` directory without a framework marker blocks with an explanatory
message; a project with neither logs "gate skipped" to stderr and allows.
