# Task 9 report — native macOS adapter

## Scope

`backends/macos.py` (113→~220 lines): pid+lstart identity via bounded
`ps`, launchctl service status, kqueue-preferred wait with ps-poll
fallback, honest capabilities, broker-gated restart.

## Delivered

- `process_list`/`process_get`: `ps -axo pid=,lstart=,comm=` argv;
  lstart → epoch; stale start_time → LookupError; `ps -p` rc≠0 with
  empty stdout → LookupError (dead pid), stderr → BackendUnavailable;
  run_bounded OSError/TimeoutExpired → BackendUnavailable; per-line
  parse failures skipped.
- `service_status`: `_LABEL` regex gate before run_bounded; fixed
  `launchctl print gui/<uid>/<label>` argv; rc≠0 → LookupError.
- `wait_process(identity, timeout_s)`: start_time required;
  verify-first reject; kqueue EVFILT_PROC/NOTE_EXIT when
  `select.kqueue` exists (real `KQ_*` constants, EV_ERROR checked,
  `kqueue()` OSError → poll fallback, process_get re-check between
  ≤250ms slices, kq closed in finally); else bounded ps poll;
  `{"ok": True, "exit_code": None}` parity with Linux.
- `restart_service` → always BackendUnavailable (broker T10).
- Capabilities: `process.wait` mode kqueue|ps-poll, `service.restart`
  supported:false broker_required, `endpoint_security`
  supported:false entitlement_required.

## Review

Independent review: Spec FAIL / Standards FAIL → fixed:

1. `select.EVFILT_PROC` nonexistent → real `KQ_FILTER_PROC`/`KQ_EV_ADD`/
   `KQ_NOTE_EXIT`; fake seam updated to mirror real API names.
2. `ps -p` rc≠0 mis-typed as BackendUnavailable → LookupError for dead
   pids (verify-first reject + mid-wait exit now correct).
3. `kqueue()` OSError → poll fallback; registration EV_ERROR → poll.
4. run_bounded exceptions typed; `int(fields[0])` guarded; exit_code
   parity; missing `subprocess` import added.
5. `start_time` required (cross-adapter parity with linux.py).

## Verification

- Held-out `test_macos_adapter.py`: 5/5 pass.
- Focused: `test_sc_macos.py` 14 + held-out 5 + inventory 16 →
  35 → 53 passed (with linux slice).
- `python -m py_compile`: clean.

## Residuals

- No real macOS host — kqueue path exercised via fake seam mirroring
  documented CPython `select` API; VM smoke deferred (plan QA gate).
- `events.process` provider inherited from earlier parity work.
