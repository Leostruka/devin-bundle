# Task 8 brief — native Linux adapter

Lead notes:
- Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`, branch `feat/system-control`.
- Follow `.devin/plans/2026-09-19-system-control.md` Task 8.
- Do not read or modify `tests/held-out/`; do not commit/PR/push.
- stdlib only. No real Linux host here — seam tests only; document that
  VM smoke is deferred to T12/CI.

Extend `extensions/system-control/backends/linux.py` (~140 → ~350
lines):

## Required changes (held-out pins these seams)

- Rename `_PROC` → `PROC_ROOT` module constant (monkeypatch seam); all
  procfs paths built from it. `_boot_time` reads
  `f"{PROC_ROOT}/stat"`.
- `process_get(pid, start_time=None)` — keep existing semantics:
  epoch seconds = btime + ticks/clk; `LookupError` dead pid;
  `LookupError("stale pid identity")` on mismatch.
- `wait_process(identity, timeout_s)` — NEW: verify identity via
  `process_get` FIRST (stale → `{"ok": False,
  "status": "rejected"}`); then prefer `os.pidfd_open` when present:
  `pidfd_open(pid)` → `os.waitid(os.P_PIDFD, fd, os.WEXITED)` if
  available else `select.select([fd],[],[],slice)` bounded loop until
  `timeout_s`; fd closed in finally. pidfd path only while pidfd_open
  exists — wrap AttributeError to the poll fallback. Poll fallback:
  re-check `process_get` liveness ≤250ms slices. Non-finite/negative
  timeout → `InvalidRequest`. Exited → `{"ok": True, "exit_code": n}`
  (waitid si_status when available).
- `service_status(name)` — keep fixed argv `["systemctl","show",name,
  "--property=ActiveState","--value"]`; keep `_systemd()` gate and
  `_SERVICE_NAME` regex (must accept `.service`/`.timer` suffixes and
  `@` instances — current regex does). `run_bounded` stays the
  injectable seam (imported name on the module).
- `capabilities()`: add `process.wait` entry — supported when procfs
  present (`mode:"pidfd"` if `hasattr(os,"pidfd_open")` else
  `"procfs-poll"`); `service.restart` NOT supported →
  `supported:false, reason:"broker_required"` (restart only via T10
  broker, never direct systemctl mutation from this adapter).
- `service.restart` capability: expose `restart_service(name, *,
  allowed)` raising `BackendUnavailable("restart requires privileged
  broker")` — never implement direct mutation.

## Tests (RED first)

`tests/test_sc_linux.py`: fake-procfs fixtures (write per-pid `stat`
with parenthesized comm incl. spaces/parens edge cases, `stat` btime),
identity roundtrip/stale/dead, pidfd preference via monkeypatched
`os.pidfd_open`, wait timeout, poll fallback when no pidfd, service
argv capture via `run_bounded` seam, systemd-gate unsupported path,
capability advertisement honesty.

## Gates

- `python -m pytest tests/test_sc_linux.py -q` → pass.
- `python -m pytest tests/test_sc_inventory.py -q` → no regression.
- `python -m py_compile backends/linux.py`.

Report: files+lines, signatures, test names/counts, residuals.
