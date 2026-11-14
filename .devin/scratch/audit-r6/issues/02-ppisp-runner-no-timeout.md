# 02 -- ppisp_runner: subprocess without timeout, OSError uncaught

- **Status**: resolved
- **Severity**: P2
- **File**: `extensions/ppisp-prep/ppisp_runner.py:93`

## Evidence

`subprocess.run(argv, cwd=up, capture_output=True, text=True)` has no
`timeout=` and no `except` around the call. A stuck upstream training
process hangs the wrapper forever; a spawn-time `OSError` (missing
interpreter/permissions) escapes as a traceback instead of the typed
JSON envelope every other extension wrapper emits.

## Fix

Add a bounded `timeout` (e.g. `PPISP_TIMEOUT` env, default 3600 -- a
training entry legitimately runs long, so keep it generous) and catch
`OSError`/`subprocess.TimeoutExpired`, returning
`{"ok": false, "error": ...}`.

## Verification

Unit test with a mocked `subprocess.run` raising `TimeoutExpired` and
`OSError` returns typed failure dicts.

## Answer

Fixed. `subprocess.run` now runs with `timeout` (PPISP_TIMEOUT env,
default 3600s, invalid values fall back) inside try/except.
TimeoutExpired -> {"ok": false, "error": "upstream_timeout:Ns"};
OSError -> {"ok": false, "error": "spawn_failed:..."}. Tests in
test_ppisp_prep.py cover timeout, spawn error, and bad env value.
