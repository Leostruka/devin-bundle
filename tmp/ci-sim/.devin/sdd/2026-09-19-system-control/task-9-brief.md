# Task 9 brief — native macOS adapter

Lead notes:
- Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`, branch `feat/system-control`.
- Follow `.devin/plans/2026-09-19-system-control.md` Task 9.
- Do not read or modify `tests/held-out/`; do not commit/PR/push.
- stdlib only. No macOS host here — seam tests only; VM smoke deferred.

Extend `extensions/system-control/backends/macos.py` (~113 → ~300):

## Required changes (held-out pins these)

- `capabilities()`: add entries — `process.wait` (supported when ps
  present; `mode:"kqueue"` if `select.kqueue` importable else
  `"procfs-poll"`-equivalent `"ps-poll"`), `endpoint_security`
  (supported False, reason `"entitlement_required"` — never attempt),
  `service.restart` (supported False, reason `"broker_required"`).
- `wait_process(identity, timeout_s)` — NEW: verify identity via
  `process_get` first (LookupError → `{"ok": False,
  "status": "rejected"}`); then if `select.kqueue` importable:
  kqueue + `EVFILT_PROC`/`NOTE_EXIT` on the pid, bounded by timeout,
  kqueue closed in finally; else bounded poll of `process_get` at ≤250ms
  slices until LookupError → `{"ok": True}` or deadline →
  `{"ok": False, "status": "timeout"}`. Non-finite/negative timeout →
  InvalidRequest.
- `service_status`: keep `_LABEL` gate before any subprocess (empty
  string must raise before run_bounded is called); keep fixed
  `launchctl print gui/<uid>/<label>` argv.
- `restart_service(name, *, allowed)` → `BackendUnavailable("restart
  requires privileged broker")` — never direct launchctl mutation.
- `process_list`/`process_get`: keep lstart parsing; no change needed
  beyond what exists unless tests require.

## Tests (RED first)

`tests/test_sc_macos.py`: capability entries (endpoint_security/
process.wait/service.restart honesty), label validation before
subprocess, wait_process poll path via fake `process_get`, kqueue path
via fake `select.kqueue` seam, stale-identity reject, bounded `log
show` argv shape if a log capability is added (otherwise omit).

## Gates

- `python -m pytest tests/test_sc_macos.py -q` → pass.
- `python -m pytest tests/test_sc_inventory.py tests/test_sc_telemetry.py -q` → no regression.
- `python -m py_compile backends/macos.py`.

Report: files+lines, signatures, test names/counts, residuals.
