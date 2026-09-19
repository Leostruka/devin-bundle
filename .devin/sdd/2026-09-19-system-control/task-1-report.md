# Task 1 report — Read-only host inventory

Status: DONE_WITH_CONCERNS (one real-backend bug found and fixed during
self-review; all gates green post-fix). No commits or staging performed —
lead owns commits.

## Files changed (all new)

- `extensions/system-control/sc_contract.py` — SCHEMA_VERSION=1, STATUSES,
  `validate_request`, `target`, `result`, `untrusted`; fail-closed ValueError.
- `extensions/system-control/sc_backend.py` — `BackendUnavailable`,
  `UnsupportedBackend`, `current()` (platform.system() → importlib),
  `capabilities(backend=None)`, `backend_name`.
- `extensions/system-control/sc_process.py` — `snapshot(*, pid=None,
  limit=100, backend=None)` returning typed verified result.
- `extensions/system-control/sc_cli.py` — `main(argv) -> int`; commands
  `capabilities`, `process-list`, `process-get`, `service-status`; one JSON
  object on stdout, diagnostics on stderr; exit 0/1/2.
- `extensions/system-control/backends/__init__.py` — `run_bounded` helper
  (argv array, shell=False, timeout=10s, output cap 1MB).
- `extensions/system-control/backends/windows.py` — Get-CimInstance JSON
  subprocess; sc.exe query for named services.
- `extensions/system-control/backends/linux.py` — /proc/<pid>/stat +
  btime-derived start_time; systemctl only when systemd detected.
- `extensions/system-control/backends/macos.py` — bounded
  `ps -axo pid,lstart,comm`; `launchctl print` for explicit labels only.
- `extensions/system-control/schemas/v1.json` — JSON Schema for
  request/result/capability_entry/target/evidence.
- `tests/test_sc_contract.py` (13 tests), `tests/test_sc_inventory.py`
  (8 tests), `tests/test_sc_cli.py` (9 tests).

## Evidence

### RED

```
$ python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q
E   ModuleNotFoundError: No module named 'sc_backend'
ERROR tests/test_sc_contract.py
ERROR tests/test_sc_inventory.py
ERROR tests/test_sc_cli.py
3 errors in 0.29s  (exit 2)
```

Expected failure: modules absent. Verified before writing production code.

### Mid-cycle RED (self-review bug)

```
$ python -m pytest tests/test_sc_inventory.py::test_windows_process_list_parses_cim_dates -q
assert (7 == 7 and 0 > 0)
1 failed  (exit 1)
```

pwsh 7 serializes CIM CreationDate as ISO-8601, not `/Date(ms)/`; the
parser silently produced `start_time: 0`. Fixed `_cim_epoch` to accept
both forms.

### GREEN

```
$ python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q
30 passed in 0.06s  (exit 0)
```

### Real-backend smoke (Windows host, no fakes)

```
$ python sc_cli.py capabilities     → ok:true status:verified, 2 caps supported
$ python sc_cli.py process-list --limit 2 → verified; start_time=1789820374 (real epoch)
$ python sc_cli.py bogus            → status:rejected, exit 2
```

### Audit

```
$ python audit.py
Errors: 0   Warnings: 2   (exit 0)
```

Warnings: `__pycache__` dirs (now includes new extension dirs — cosmetic),
`v3.1.1 tag missing` (pre-existing worktree state, unrelated).

### Full repository suite (Rule 5)

```
$ python -m pytest -q
612 passed, 1 skipped in 101.69s  (exit 0)
```

Skipped: `test_cu_screenshot` (pre-existing). Held-out
`tests/held-out/system-control/test_identity_and_confirmation.py`
collected and passed (2 tests) — not read or modified.

## Self-review

- Stdlib only; no dependencies added; no imports from computer-use.
- pid+start_time enforced in contract, CLI (`--pid`+`--start-time`
  together) and adapters (stale identity → LookupError → value null).
- Unknown command/version/backend → typed rejected/unsupported, never
  fallback shell. `UnsupportedBackend` raises BackendUnavailable on use.
- External commands: argv arrays, shell=False, timeout, capped output.
- Exactly one JSON object on stdout per CLI invocation; errors to stderr.
- Procedural style; only class is `UnsupportedBackend` (state: name+reason,
  implements backend protocol) — justified by manifest rule.
- No AI signatures; no secrets.

## Concerns

1. Brief asked to stage lead-owned plan/research/held-out files; handoff
   said do not stage. Followed handoff — nothing staged.
2. `sc_process.snapshot` returns `request_id=None` when called directly;
   CLI assigns its own request_id after the call (per exact interface).
   — superseded by fix round 1 finding 3: snapshot now generates a
   non-null request_id; CLI still overwrites with its own.
3. macOS/Linux adapters are written to spec but only Windows paths were
   exercised on real OS calls; POSIX adapters covered by unit seams only.
4. `service.observe` on Windows relies on sc.exe output parsing — per
   plan, allowed only until native API lands in T7.

---

# Fix round 1 — reviewer findings

All 9 findings addressed. 17 new tests; TDD: tests written and observed
failing before implementation.

## Changes

1. **IMPORTANT — typed request-validation seam:** added
   `sc_contract.InvalidRequest(ValueError)`. `validate_request`,
   `target`, CLI arg parsing (`_opts`, `_int_arg`, missing/trailing/
   duplicate/unknown args), and backend service-name/pid/start_time
   validation raise it → CLI exit 2. Backend output parse failures
   (malformed /proc, bad CIM dates, JSON errors) remain plain
   errors → exit 1. Tests: `test_invalid_request_is_typed_valueerror`,
   `test_cli_backend_valueerror_is_runtime_not_rejected`,
   `test_cli_invalid_request_validation_exit_2`,
   `test_service_name_validation_uses_invalid_request`.
2. Timeout: `run_bounded` raises `subprocess.TimeoutExpired` after
   kill+wait; CLI maps it to `status:"timeout"`, exit 1.
   Test: `test_cli_subprocess_timeout_maps_to_timeout`.
3. `sc_process.snapshot` now emits `uuid4` request_id for direct
   callers (signature unchanged). Test:
   `test_snapshot_generates_request_id_for_direct_callers`.
4. Strict per-command flags: `_opts(argv, allowed)` rejects unknown,
   duplicate, missing-value flags and trailing positionals;
   `capabilities` rejects any args; `service-status` requires exactly
   one positional. Tests: `test_cli_rejects_{trailing_args,
   unknown_flag, duplicate_flag, extra_positional, non_integer_flag}`.
5. `validate_request` rejects extra `target` keys (matches schema
   `additionalProperties: false`). Test: `test_target_rejects_extra_keys`.
6. `run_bounded` rewritten: `Popen` + two daemon drain threads that
   always read to EOF (no pipe deadlock) while retaining ≤cap bytes;
   timeout kills, reaps, then raises TimeoutExpired carrying partial
   capped output. Tests with real `sys.executable` children:
   `test_run_bounded_caps_output_but_drains` (200KB stdout+stderr,
   cap=1000), `test_run_bounded_timeout_kills_child` (sleep 60 killed
   at timeout=1).
7. Linux `process_list` reads `/proc/stat` btime once per call;
   `_read_proc(pid, boot)` takes it as parameter. Seam test:
   `test_linux_boot_time_read_once_per_scan` (fake /proc tree +
   counting `_boot_time`; asserts single call, correct start_times).
8. `_cim_epoch` raises `BackendUnavailable` on unparseable CreationDate
   instead of returning 0 → backend read fails → CLI exit 1.
   Test: `test_windows_unparseable_cim_date_fails_read`.
9. CLI tracks resolved `name` (default `"none"`); all post-resolution
   error envelopes carry it. Test:
   `test_cli_backend_error_keeps_backend_name` (asserts `"fake"`).

## Fix-round evidence

RED (new tests before implementation):

```
$ python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q
14 failed, 33 passed  — all failures for expected missing behavior
```

GREEN:

```
$ python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q
47 passed in 1.27s  (exit 0)
```

First full-suite run exposed a test-identity bug (not implementation):
held-out loaders register their own `sc_contract` module instance, so
two tests asserting `contract.InvalidRequest` identity failed
(2 failed / 627 passed). Fixed tests to bind the exception through the
module under test (`windows.InvalidRequest`, `sc_cli.contract.InvalidRequest`)
— identity-safe regardless of loader ordering.

Ordering repro:

```
$ python -m pytest tests/held-out/system-control/ tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q
49 passed in 1.20s  (exit 0)
```

Final gates:

```
$ python audit.py
Errors: 0   Warnings: 2   (exit 0)

$ python -m pytest -q
629 passed, 1 skipped in 101.19s  (exit 0)
```

Skipped: `test_cu_screenshot` (pre-existing). Warnings unchanged
(__pycache__ dirs; v3.1.1 tag absent in worktree).

## Self-review (round 1)

- Exit-code contract now clean: 2 = InvalidRequest (user/CLI/request
  validation incl. backend arg validation), 1 = runtime (backend parse,
  OS errors, timeouts with status:"timeout"), 0 = verified.
- `run_bounded` drains both pipes concurrently to EOF — no deadlock on
  >pipe-buffer output; retained bytes capped; child killed+reaped on
  timeout; partial output attached to the exception.
- All original requirements intact: stdlib only, one JSON object on
  stdout, pid+start_time identity, fail-closed dispatch, no deps.
- No commits/staging performed; held-out untouched.

## Concerns (round 1)

1. Two `run_bounded` behavior tests passed even under the old
   capture_output implementation (they verify the contract — caps,
   draining, timeout — not the mechanism). The Popen+threads mechanism
   is implemented per the finding; observable difference is memory
   bound, which tests cannot cheaply prove.
2. Same module-instance caveat as above applies to any future test
   asserting exception identity across test files — bind through the
   module under test.
3. POSIX adapters still verified via seams only (Windows host).

---

# Fix round 2 — fail-closed gaps

Two findings, both addressed with TDD (5 new/changed tests observed
failing first).

## Changes

1. **`process-get` LookupError → rejected:** stale `pid+start_time`
   identity or missing process now returns `status:"rejected"`, exit 2,
   resolved backend name preserved, non-sensitive reason in `error`
   (e.g. "stale pid identity", "process not found: 7"). Was previously
   `verified` + `value:null`. Updated test
   `test_cli_process_get_stale_identity_rejected`; new
   `test_cli_process_get_not_found_rejected`.
2. **Non-negative identity/limit everywhere:** CLI `_int_arg` rejects
   negatives (`--pid`, `--start-time`, `--limit`); `sc_process.snapshot`
   rejects `limit<0` via `InvalidRequest`; all three adapters validate
   pid/start_time through a shared `_nonneg_int` → `InvalidRequest`
   (linux validates pid before touching `/proc/stat`). Zero still
   allowed (schema min 0). Tests:
   `test_cli_rejects_negative_identity_and_limit` (4 argv cases),
   `test_backends_reject_negative_identity` (3 adapters × pid and
   start_time), `test_snapshot_rejects_negative_limit`.

## Fix-round evidence

RED (before implementation):

```
$ python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q
5 failed, 46 passed  — stale/not-found verified-null and negatives accepted
```

GREEN:

```
$ python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q
51 passed in 1.18s  (exit 0)
```

Final gates:

```
$ python audit.py
Errors: 0   Warnings: 2   (exit 0)

$ python -m pytest -q
633 passed, 1 skipped in 102.03s  (exit 0)
```

Skipped: `test_cu_screenshot` (pre-existing). Warnings unchanged.

## Self-review (round 2)

- Identity binding is now fail-closed end to end: CLI rejects
  negative/missing identity before dispatch; backends re-validate
  direct callers; LookupError never masquerades as a verified read.
- Exit codes unchanged in meaning: 0 verified, 1 runtime/timeout,
  2 rejected.
- No held-out reads/edits; nothing staged or committed.

## Concerns (round 2)

1. `linux.process_list(pid=<bad>)` on a host without `/proc` still
   reports `/proc not mounted` before pid validation — acceptable
   ordering (capability absence reported before arg checking).
2. `LookupError` messages pass through backend strings verbatim —
   currently pid/name only; future adapters must keep reasons
   non-sensitive.
