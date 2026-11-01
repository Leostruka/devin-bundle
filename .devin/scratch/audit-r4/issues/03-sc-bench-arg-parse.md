# Issue: sc_bench.py manual arg parsing crashes on non-int values

- **Severity**: P3
- **Status**: resolved
- **File**: `extensions/system-control/sc_bench.py`

## Evidence

`_main` (lines 74-90) parses argv manually:

```python
runs, warmup = 30, 5
args = iter(argv)
...
    if a == "--runs":
        runs = int(next(args, "30"))
```

`--runs abc` -> `ValueError` traceback; `--runs` with no value silently
defaults (arguably fine) but a trailing non-numeric always crashes.
Dev-only bench tool, low impact -- but same untyped-input class.

## Acceptance

- Non-numeric `--runs`/`--warmup` -> typed error message on stderr or
  JSON error, non-zero exit, no traceback
- Regression test: `sc_bench --runs abc` exits non-zero without traceback

## Answer

Fixed. `--runs`/`--warmup` parsing wrapped in try/except ValueError ->
`{"ok": false, "error": "bad_arg:..."}` on stdout + exit 2, no
traceback. Regression test `test_non_numeric_runs_typed_error` in
`tests/test_sc_bench.py`.
