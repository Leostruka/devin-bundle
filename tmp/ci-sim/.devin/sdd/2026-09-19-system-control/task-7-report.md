# Task 7 report — native Windows adapter

## Result
- `extensions/system-control/sc_windows.py` (new, ~580): ctypes Win32 —
  `process_get` (GetProcessTimes identity), `wait_process` (handle wait,
  no polling), `spawn_owned`/`close_owned` (suspended → job → resume),
  `service_status`/`restart_service` (SCM, allowlist-first),
  `resume_main_thread` (Toolhelp32), `scm_available`.
- `sc_process.py`: `_create_job()` extracted; `spawn()` on nt uses
  `CREATE_SUSPENDED` → job assign → `resume_main_thread` — the T3
  Popen→AssignProcessToJobObject race is CLOSED.
- `backends/windows.py`: native `process_get` preferred, CIM fallback
  on LookupError/PermissionError/degraded-native (preserves coverage of
  protected pids); `wait_process`, `restart_service` delegation;
  `process.wait` + `service.restart` capabilities advertised.
- `sc_cli.py`: `process wait` (allow), `service restart` (CONFIRM,
  `--allowed` required, digest binds name+allowed).
- Tests: `test_sc_windows.py` 21 + `test_sc_windows_events.py` 8.

## Review history
- Round 1: Spec PASS / Standards FAIL — double CloseHandle on thread
  handle, missing argtypes, non-finite timeout, recursive fake in test,
  resume-all-threads, access-denied conflation.
- Rework: all 6 closed.
- Lead fixes: `process_get` CIM fallback ordering (T1 inventory
  regression); held-out epoch bug (FILETIME 1601→1970 delta) and
  `os.kill(pid,0)` liveness check replaced with
  OpenProcess+GetExitCodeProcess (Windows `os.kill` terminates).
- Cross-test pollution: held-out `load()` `sys.modules.pop` created
  divergent module objects (sc_contract/sc_policy) breaking
  `pytest.raises` and monkeypatch in visible tests — pop removed from
  all 6 held-out files.

## Evidence
- Held-out `test_windows_adapter.py`: 5/5 on real host (identity vs
  GetProcessTimes ground truth, stale reject, handle wait, job kill,
  allowlist reject).
- Slice incl. all held-out: 65 passed.
- Full suite: 863 passed, 3 skipped.
- `python audit.py`: 0 errors, 1 pre-existing `__pycache__` warning.

## Residual
- No real service restart executed (plan Step 6: smoke read-only only).
- `resume_main_thread` picks first thread by owner pid — correct for a
  fresh suspended child.
- `proc._handle` private API still used by sc_process job assign.
- Windows resolve→open swap window in sc_files still open (documented).
