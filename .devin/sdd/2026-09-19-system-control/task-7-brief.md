# Task 7 brief — native Windows adapter

Lead notes:
- Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`, branch `feat/system-control`.
- Follow `.devin/plans/2026-09-19-system-control.md` Task 7.
- Do not read or modify `tests/held-out/`; do not commit/PR/push.
- stdlib + ctypes only (no pywin32).

Create `extensions/system-control/sc_windows.py` — ctypes Win32 layer —
and wire it into `backends/windows.py` and `sc_process.py`. Target
~400 lines new + ~80 wiring.

## `sc_windows.py` (held-out pins this surface)

- `process_get(pid, start_time=None) -> dict`
  - `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION=0x1000)` →
    `GetProcessTimes` → creation FILETIME → epoch seconds;
    `QueryFullProcessImageNameW` for `name`. `LookupError` on dead pid;
    stale `start_time` → `LookupError("stale pid identity")` or
    `{"status":"rejected"}` — pick one shape, stay consistent (suggest
    LookupError, matching `backends/windows.py`).
  - Every handle closed in `finally`.
- `wait_process(identity, timeout_s) -> {"ok": True, "exit_code": int}`
  - Verify `identity["start_time"]` matches live creation time BEFORE
    waiting (PID-reuse guard) → mismatch → `{"ok": False,
    "status": "rejected"}`.
  - `WaitForSingleObject(handle, timeout_ms)` — never PID polling.
    Timeout → `{"ok": False, "status": "timeout"}`.
- `spawn_owned(argv, *, cwd=None) -> dict` — the race-free spawn:
  `CreateProcessW` via a `subprocess.Popen` shim is NOT required here;
  implement with ctypes `CreateProcessW` + `STARTUPINFOW` +
  `CREATE_SUSPENDED`, assign the process handle to a fresh Job Object
  (`sc_process._new_job`/`_assign_tree` pattern — extract a shared
  `_create_job()` helper in `sc_process` if useful), `ResumeThread`,
  close thread handle. Return `{"ok": True, "pid", "start_time",
  "job": job_handle_int, "process": proc_handle_int}` — document that
  callers own both handles and must `close_owned`.
  - Any failure between create and resume → `TerminateProcess` +
    close both handles + close job (fail-closed, no suspended orphan).
- `close_owned(s) -> {"ok": True}` — `TerminateJobObject`/`CloseHandle`
  on job (KILL_ON_JOB_CLOSE reaps the tree) + close process handle.
- `service_status(name) -> dict` — SCM via ctypes:
  `OpenSCManagerW(SC_MANAGER_CONNECT)` + `OpenServiceW(SERVICE_QUERY_STATUS)`
  + `QueryServiceStatusEx`; close all handles finally. Name validated
  against `^[A-Za-z0-9_.\-]+$`.
- `restart_service(name, *, allowed) -> envelope`
  - `name not in allowed` → `{"ok": False, "status": "rejected"}` —
    before any SCM call. `allowed` empty/None → always reject.
  - STOP via `ControlService`, bounded wait through pending states
    (poll QueryServiceStatusEx ≤30s, 250ms), START via `StartServiceW`,
    wait to RUNNING; return `{"ok": True, "status": "verified",
    "precondition": {"state": ...}, "postcondition": {"state": ...}}`.
    Never touch service config/identity.
- `resume_main_thread(pid)` helper for `sc_process` (below):
  Toolhelp32 `CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD)` →
  `Thread32First/Next` find thread with `th32OwnerProcessID==pid` →
  `OpenThread(THREAD_SUSPEND_RESUME=0x0002)` → `ResumeThread` →
  close. Raise on any step failure.

## `sc_process.py` — close the Popen→Job race (T3 deferred)

On `os.name == "nt"`: add `subprocess.CREATE_SUSPENDED` to
`creationflags` in `spawn()`; after Popen returns, `_assign_tree` with
the suspended handle, THEN `sc_windows.resume_main_thread(proc.pid)`.
On any post-spawn failure: `proc.kill()` (suspended proc killable) +
job cleanup + preserve original exception. POSIX path unchanged.

## `backends/windows.py` — prefer native

`process_get`/`process_list` keep the CIM fallback; add
`wait_process(identity, timeout_s)` delegating to `sc_windows` when
importable, else `BackendUnavailable`. Advertise `process.wait` and
`service.restart` in `capabilities()` (restart: `mode:"scm"`,
supported when SCM opens). `service.restart` must flow through
`sc_windows.restart_service` with an allowlist arg from the request.

## CLI (`sc_cli.py`)

- `process wait --pid N --start-time T [--timeout S]` → `process.wait`
  (allow).
- `service restart --name S --allowed S1,S2 --confirmation-id ID
  --request-id R` → `service.restart` (CONFIRM; binds name+allowed).
  `--allowed` required — no implicit allowlist.

## Visible tests (RED first)

`tests/test_sc_windows.py` + `tests/test_sc_windows_events.py` —
real-host tests (skip if `os.name != "nt"` where needed): own-pid
process_get vs ctypes ground truth; stale start_time rejected;
wait_process returns on real child exit + timeout path; spawn_owned
child dies on close_owned (job kill); suspended-spawn race probe
(child that writes instantly — assert no output escapes before resume:
spawn suspended-flagged process writing to a file, assert file absent
while suspended); service_status on a known service (e.g. "wuauserv"
or query sc.exe for one present); restart allowlist rejection without
SCM call; handle-leak check (spawn+close N times, assert handle count
stable via GetProcessHandleCount or just loop 50x without exception).

`sc_process` regression: existing exec tests must still pass with
suspended+job spawn.

## Gates

- `python -m pytest tests/test_sc_windows.py tests/test_sc_windows_events.py -q` → pass.
- `python -m pytest tests/test_sc_process_exec.py -q` → no regression.
- `python -m py_compile` touched files.

Report: files+lines, signatures, test names/counts, residuals.
