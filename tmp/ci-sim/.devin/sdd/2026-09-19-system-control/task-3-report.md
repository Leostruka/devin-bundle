# Task 3 Report — Bounded one-shot process execution

Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`
Base: Task 2 at `b8867ab`, branch `feat/system-control`

## Files changed

Modified:
- `extensions/system-control/sc_process.py` — added `spawn`, `wait`,
  `cancel`; validation helpers (`_valid_argv`, `_valid_num`,
  `_valid_dir`, `_safe_env`); Windows Job Object ownership
  (`_job_assign`, `TerminateJobObject`/`CloseHandle` cleanup); POSIX
  `start_new_session` + `killpg` TERM→grace→KILL; bounded reader
  threads with tail cap + owner-only spill; `_finalize_spill`
  (single-stream passthrough, combined file with ASCII section
  headers). `snapshot` unchanged.
- `extensions/system-control/sc_cli.py` — `exec` command: strict flags
  (`--argv-json`, `--request-id`, `--confirmation-id` required;
  `--cwd`, `--timeout` optional), builds the exact briefed request,
  `classify` must return `confirm`, `consume_confirmation` must return
  `ok`, then `sc_process.spawn`; result request_id overwritten with the
  supplied ID; exit 0 iff `ok`, exit 1 on timeout/nonzero, exit 2 on
  any rejection. `backend` reported as `"subprocess"`. Runs before OS
  backend discovery (policy/subprocess path only).
- `tests/test_sc_cli.py` — 6 exec tests (no-confirmation reject,
  consume-once + replay reject, argv/cwd/timeout/request_id mutation
  reject, strict flags, bad argv JSON).

Created:
- `tests/test_sc_process_exec.py` — 21 tests covering argv validation
  (string/tuple/empty/NUL), numeric bounds incl. bool/NaN/Infinity,
  cwd/spill_dir resolution without creation, env baseline +
  secret-class rejection, Popen kwargs (shell=False, DEVNULL stdin,
  PIPEs, platform flags), semicolon/`$()` as literal args, result
  shape, nonzero→unknown, timeout→timeout with tree kill verified via
  real backend, flood spill (combined, exact byte equality), single
  spill, concurrent dual-pipe drain, wait/cancel seams, idempotent
  cancel, env value non-leakage.

## RED

```
python -m pytest tests/test_sc_process_exec.py tests/test_sc_cli.py -q
```

```
22 failed, 32 passed in 0.50s
FAILED test_spawn_rejects_bad_argv .. AttributeError: module
  'sc_process' has no attribute 'spawn' (all spawn/wait/cancel tests)
FAILED test_cli_exec_*  — unknown command / rejected
```

Expected: `spawn`/`wait`/`cancel` and the `exec` command absent.

## GREEN

```
python -m pytest tests/test_sc_process_exec.py tests/test_sc_policy.py tests/test_sc_cli.py tests/test_sc_contract.py tests/test_sc_inventory.py -q
```

```
============= 110 passed in 14.84s =============
(exec 21, policy 25, cli 33, contract 15, inventory 16)
```

One mid-cycle fix: `test_env_only_baseline_plus_allow` asserted the
literal string `"1"` absent from the JSON result — trivially present
in numeric fields. Test defect (not production); the leak guarantee is
covered by `test_env_values_never_in_result` with a unique sentinel.

## Audit

```
python audit.py   →  exit 0
Errors: 0   Warnings: 1 (pre-existing __pycache__ dirs only)
```

## Full suite

```
python -m pytest -q
============= 698 passed, 1 skipped in 73.77s =============
```

Skip is the pre-existing `test_cu_screenshot` environment skip.
Held-out `system-control` files (identity/confirmation,
paths/output) all pass; never read or edited.

## Live Windows checks (real OS, not seams)

- **Job Object timeout tree kill** —
  `test_spawn_timeout_cleans_tree` spawns `python -c` which launches a
  grandchild `python -c 'sleep(60)'`, prints the grandchild PID, then
  sleeps. `timeout_s=1` → status `timeout`; test then polls the real
  Windows backend `process_list()` for both the root PID and the
  grandchild PID — both disappear within 5 s (Job Object
  `KILL_ON_JOB_CLOSE` + `TerminateJobObject` kills the whole tree).
  PASSED.
- **Output flood** — `test_spawn_output_flood_spills_combined` writes
  200 KB to each pipe (>> pipe capacity) with `output_limit=1000`:
  tails are exactly the last 1000 bytes, `stdout_bytes`/
  `stderr_bytes` = 200000, `dropped` = 398000, and the combined
  owner-only spill file equals
  `=== stdout ===\n + 200000 A's + \n=== stderr ===\n + 200000 B's + \n`
  byte-for-byte; intermediate files removed. PASSED.
- **Concurrent drain** — `test_concurrent_drain_no_deadlock` floods
  stdout and stderr simultaneously (300 KB each); would deadlock under
  serial draining. PASSED.
- All spawned children reaped; no daemon/server persists (suite
  teardown clean, tmp dirs empty except final spill files under
  pytest `tmp_path`).

## Security self-review

- argv-only: list validated (non-empty, non-empty str items, no NUL);
  `shell=False` always; semicolon/`&`/`$()` confirmed literal via
  child `sys.argv` echo. No string command ever reaches Popen.
- stdin is `DEVNULL`; no inherited stdin, no password path.
- Environment: explicit baseline whitelist copied only when present;
  `env_allow` rejects non-dict, empty/NUL keys, NUL values, non-str
  values, and the secret-class regex (case-insensitive) — all with
  `InvalidRequest("environment key is not allowed")` before `Popen`.
  Env values never appear in the result (sentinel test).
- cwd/spill_dir: `expanduser().resolve(strict=True)` + `is_dir()`;
  caller-specified dirs are never created.
- Numeric bounds: `timeout_s` finite non-bool `(0,300]`,
  `output_limit` int `(0,1048576]`, `grace_s` finite `(-1,30]`
  i.e. `0..30`; bool/NaN/Infinity rejected.
- Ownership: Windows Job Object `KILL_ON_JOB_CLOSE` assigned
  immediately after `Popen`; on assign failure the child is killed,
  reaped, and the error raised — never continues unowned. POSIX uses
  `start_new_session` + `killpg` TERM→grace→KILL. No `taskkill`, no
  shell.
- Cancellation acts on the retained process/job handle, never a PID
  lookup; `target` = `{pid, time.time_ns() nonce}` as evidence.
- Output: concurrent drain, tail-capped memory, spill via `mkstemp`
  (0600 POSIX; Windows inherits dir ACLs), complete stream(s)
  persisted, intermediate files removed on combine.
- `stdout`/`stderr` wrapped `contract.untrusted`; `evidence.dropped`
  counts omitted inline bytes.
- Zero exit → `dispatched` (never `verified` — no postcondition
  verified beyond exit observation); nonzero → `unknown` +
  `process exited with code N`; timeout → `timeout`.
- CLI: confirmation consumed (single-use, digest-bound to the exact
  request incl. argv/cwd/timeout/request_id) before `Popen`; replay or
  any mutation → rejected exit 2 before spawn. Preflight and exec
  failure paths spawn nothing.
- `--timeout` normalized to int when integral so the CLI-built request
  digest matches an issued `timeout_s: 30` int; non-finite rejected
  before `deadline_ms` computation.
- Result never contains the process object (json.dumps round-trip
  asserted).

## Rework round 1 (independent review)

1. **Truthful tree cleanup** — `_reap_tree` now returns `bool` and
   caches `tree["cleanup"]` for idempotence. Windows: TerminateJobObject
   result recorded (failure recoverable via close, since
   KILL_ON_JOB_CLOSE applies); `tree["closed"]` set only on successful
   `CloseHandle`; cleanup true only if root reaped AND handle closed.
   POSIX: `ProcessLookupError`/`ESRCH` treated as absent, other signal
   errors → false; root reaped; group absence verified with bounded
   `killpg(pid, 0)` checks. `cancel`/`wait` propagate the bool —
   nothing hardcodes `tree_cleanup=True`. Injected-seam tests (Win32):
   close failure → false (no `closed` set, no re-attempt on second
   call — `fake.calls == ["terminate", "close"]`), terminate failure
   recovered by close → true, zombie root (wait always times out, kill
   noop) → false.
2. **Exception-path ownership** — after `Popen` + `_assign_tree`
   succeed, reader startup + wait + finalize + result-build run under
   try/except: any unexpected exception calls `_reap_tree`, closes both
   streams, joins started readers boundedly, re-raises.
   `_start_readers` appends state to `handle["readers"]` before each
   `Thread.start()` so partial readers are visible to cleanup; a
   failed start closes that stream. Tests: injected `proc.wait`
   RuntimeError (`WaitBoom` proxy — child reaped via `poll()`) and
   second-reader `Thread` construction failure (`rec.proc.poll()` not
   None).
3. **`validate_spawn`** — public pure-validation helper returning
   normalized `{argv, cwd, env, timeout_s, output_limit, spill_dir}`;
   `spawn` calls it; CLI calls it before building/consuming the
   confirmation (raw cwd kept in the canonical request). New test
   `test_cli_exec_invalid_input_never_consumes_token`: invalid argv /
   cwd / timeout / NaN each reject exit 2 with the token file still
   present, then the same token dispatches successfully. Env mapping
   is internal to spawn — never serialized to CLI output.
4. **Grace bounds** — `_valid_num` gained `inclusive_lo`; `grace_s`
   is `[0, 30]` — `-0.5` and `-1` rejected, `0` and `30` accepted.
5. **Reader join hardening** — `_join_reader`: bounded join, then
   owner-side `stream.close()` + one more bounded join; eof false if
   still alive. Same closure used in exception cleanup; output never
   reported complete while a reader lives.
6. **Reader-failure cleanup coverage** —
   `test_reader_failure_still_cleans_tree` patches `_reader_run` to
   error immediately; sleeping child + `timeout_s=1` → status
   `timeout`, `tree_cleanup: True`, child reaped (`poll()` not None).
7. Popen→Assign race remains a documented residual for Task 7 (no
   custom CreateProcess here).

### Rework RED/GREEN notes

New tests were written alongside the rework; first combined run after
implementation caught two defects in my own changes (non-numeric
`_valid_num` comparison raising `TypeError` instead of
`InvalidRequest`; missing `threading` import in the test file) —
fixed, then:

```
python -m pytest tests/test_sc_process_exec.py tests/test_sc_policy.py tests/test_sc_cli.py tests/test_sc_contract.py tests/test_sc_inventory.py -q
============= 117 passed in 16.03s =============
(exec 27, policy 25, cli 34, contract 15, inventory 16)

python audit.py   →  exit 0
Errors: 0   Warnings: 1 (pre-existing __pycache__ dirs)

python -m pytest -q
============= 705 passed, 1 skipped in 62.65s =============
(pre-existing test_cu_screenshot skip; held-out untouched)
```

Live failure-seam evidence (Windows): `WaitBoom` wait injection →
child polled dead; `Thread` start injection → child polled dead;
injected Job close failure → `tree_cleanup` false with root still
reaped. POSIX group-kill path unchanged in coverage (Windows host).

## Rework round 2 (final review cleanup)

1. **Never join an unstarted reader** — `state["started"]` set only
   after a successful `Thread.start()`; `_join_reader` skips threads
   that never started (`Thread.join` on unstarted threads raises).
   Original start exception preserved and re-raised. New test
   `test_spawn_thread_start_failure_reaps_child` injects
   `Thread.start` failure (not constructor): original
   `RuntimeError("start boom")` surfaces, child polled dead.
2. **Spill close errors mark capture incomplete** — in
   `_reader_run`'s finally, a `spill_fh.close()` failure is recorded
   to `state["error"]` when none exists. Seam test
   `test_reader_spill_close_error_marks_incomplete` wraps the spill fh
   via `_open_spill`: result `unknown` / `output capture incomplete`,
   never `dispatched`, `tree_cleanup` still true.
3. **Partial artifact cleanup** — `_unlink_retry` (bounded 5-attempt
   unlink, FileNotFoundError = done). `_finalize_spill`: on any
   combine failure, fd/ handle closed, partial combined file and both
   intermediates deleted, then re-raise; an intermediate that survives
   `_unlink_retry` now *fails* finalization (OSError) and triggers the
   same cleanup — no success-with-residue. `_open_spill` closes the
   mkstemp fd if `fdopen` fails. `spawn`'s outer except deletes all
   reader spill paths plus any finalized `spill_path`. Test
   `test_finalize_combine_failure_cleans_all` injects
   `copyfileobj` failure mid-combine: `OSError` propagates, spill dir
   empty, child reaped. Success path no-leftovers already asserted in
   `test_spawn_output_flood_spills_combined`.

### Rework-2 gates

```
python -m pytest tests/test_sc_process_exec.py tests/test_sc_policy.py tests/test_sc_cli.py tests/test_sc_contract.py tests/test_sc_inventory.py -q
============= 120 passed in 16.13s =============
(exec 30, policy 25, cli 34, contract 15, inventory 16)

python audit.py   →  exit 0
Errors: 0   Warnings: 1 (pre-existing __pycache__ dirs)

python -m pytest -q
============= 708 passed, 1 skipped in 63.54s =============
(pre-existing test_cu_screenshot skip; held-out untouched)
```

## Concerns

1. POSIX job-group path (`start_new_session`, `killpg`, SIGKILL
   escalation) is written to spec but exercised only on Windows; POSIX
   verification deferred to a POSIX host/CI.
2. Windows spill files rely on directory ACLs (mkstemp semantics are
   POSIX-0600); same best-effort caveat as Task 2 tokens.
3. `proc._handle` is a CPython-private attribute used for
   `AssignProcessToJobObject`; stable across supported versions but
   non-public API.
4. ~~`exec` burns the token on invalid spawn args~~ — resolved in
   rework: `validate_spawn` runs before consume; token preserved.
5. Residual per review: the Popen→AssignProcessToJobObject window lets
   a fast child fork a descendant before job assignment; deferred to
   Task 7 (suspended-create or equivalent), not custom CreateProcess
   here.
