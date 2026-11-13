# Task 8 report — native Linux adapter

## Scope

`backends/linux.py` (140→~255 lines): procfs identity, pidfd-preferred
wait, honest capabilities, broker-gated service restart.

## Delivered

- `PROC_ROOT` seam; all procfs paths built from it.
- `_parse_stat` `rfind(")")` — comm with parens/spaces parses correctly.
- Identity: `btime + ticks // SC_CLK_TCK` epoch; dead → LookupError,
  stale → LookupError("stale pid identity"); parse failures →
  LookupError (never raw ValueError/IndexError).
- `wait_process(identity, timeout_s)`: start_time required
  (InvalidRequest); verify-first reject; `pidfd_open` →
  `waitid(P_PIDFD)` (OSError → `{"ok": True, "exit_code": None}` for
  5.3–5.4 kernels) else select slices; post-open stat re-verify catches
  reaped+reused pid; procfs-poll fallback, ≤250ms slices, monotonic
  deadline; fd always closed.
- `service_status`: regex gate before `_systemd()`/run_bounded; fixed
  `systemctl show <name> --property=ActiveState --value` argv.
- `restart_service` → always BackendUnavailable (broker T10).
- Capabilities: `process.wait` (pidfd|procfs-poll), `service.restart`
  supported:false `broker_required`.

## Review

Independent review: Spec PASS, Standards FAIL → fixed:

1. `waitid` EINVAL on 5.3–5.4 kernels → caught, fd-ready proves exit.
2. Stat parse failures now typed LookupError.
3. Post-open stat re-verify closes verify→open reuse window.
4. `start_time` required at backend (was wire-only).
5. `_boot_time` moved outside try; `//` division; macOS adapter
   received the same start_time gate (cross-adapter parity).

## Verification

- Held-out `test_linux_adapter.py`: 6/6 pass.
- Focused: `tests/test_sc_linux.py` + `tests/test_sc_inventory.py`
  + held-out → 40 → 59 passed (incl. T9 files at final run).
- `python -m py_compile`: clean.
- Full suite + audit: recorded in ledger below.

## Residuals

- `_boot_time` OSError surfaces raw in `process_list` (procfs absent →
  BackendUnavailable via `isdir` guard first); acceptable.
- No live-Linux VM smoke; seams cover logic.
