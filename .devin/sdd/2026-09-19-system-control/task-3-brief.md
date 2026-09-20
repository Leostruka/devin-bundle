# Task 3 brief — Bounded one-shot process execution

## Context

Task 2 is complete at `b8867ab`. Add one-shot argv-only execution. This slice owns subprocesses; persistent sessions remain Task 4.

## Binding constraints

- Python 3.9+ stdlib only; procedural/functional style.
- Never pass a string command. Always `shell=False`.
- No implicit elevation, shell expansion, password handling, or inherited stdin.
- Environment starts from an explicit safe baseline only.
- Reject secret-class environment names before spawn.
- Validate cwd exists, resolves, and is a directory before spawn.
- Drain stdout and stderr concurrently; memory remains bounded.
- Default tail cap: 16000 bytes per stream.
- On overflow, retain tail and write complete stream(s) to owner-only spill.
- Timeout and normal completion both clean the owned process tree.
- Windows: Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
- POSIX: `start_new_session=True`, process-group TERM → grace → KILL.
- External output is wrapped with `contract.untrusted`.
- A zero exit only returns `status:"dispatched"`; no postcondition means never `verified`.
- CLI must consume an exact Task 2 confirmation before `Popen`.
- No mutation occurs on preflight, confirmation failure, or dry-run.
- Do not read/edit `tests/held-out/`, plan, research, installers, docs, or computer-use.
- No staging or commit; lead owns commits.

## Files

Modify:
- `extensions/system-control/sc_process.py`
- `extensions/system-control/sc_cli.py`
- `tests/test_sc_cli.py`

Create:
- `tests/test_sc_process_exec.py`

Update evidence only:
- `.devin/sdd/2026-09-19-system-control/task-3-report.md`

## Exact public interfaces

Keep existing `snapshot` unchanged.

```python
def spawn(argv: list[str], *, cwd=None, env_allow=None, timeout_s=30,
          output_limit=16000, spill_dir=None, backend=None) -> dict: ...
def wait(handle: dict, *, timeout_s=30, backend=None) -> dict: ...
def cancel(handle: dict, *, grace_s=2, backend=None) -> dict: ...
```

`backend` is an injectable subprocess-like seam. Production uses `subprocess`; tests may provide an object exposing `Popen`, `PIPE`, and `DEVNULL`. `wait` and `cancel` operate on the runtime-only internal handle created by `spawn`; they are public for unit seams, but the returned result never serializes the process object.

## Validation

### argv

- Must be a non-empty `list`.
- Every item must be a non-empty `str` without NUL.
- Reject tuples and command strings.

### Numeric values

- `timeout_s`: finite int/float, bool rejected, `0 < value <= 300`.
- `output_limit`: int, bool rejected, `1..1048576`.
- `grace_s`: finite int/float, bool rejected, `0..30`.

### cwd/spill

- `cwd`: `Path(cwd).expanduser().resolve(strict=True)` and `is_dir()`.
- `spill_dir`: same validation; default `tempfile.gettempdir()`.
- Never create caller-specified directories.

### environment

Safe baseline copied only when present:
```python
_ENV_BASELINE = (
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "LANG", "LC_ALL", "TMPDIR",
)
```

`env_allow` defaults to `{}` and must be `dict[str, str]`. Reject empty/NUL keys, NUL values, and names matching this case-insensitive regex:
```python
r"(^|_)(SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE_KEY|API_KEY|AUTH|COOKIE)($|_)"
```
Raise `contract.InvalidRequest("environment key is not allowed")`. Never return environment values or inherited environment contents.

## Process ownership

Production `Popen` kwargs:
```python
{
    "args": argv,
    "cwd": resolved_cwd,
    "env": safe_env,
    "stdin": subprocess.DEVNULL,
    "stdout": subprocess.PIPE,
    "stderr": subprocess.PIPE,
    "shell": False,
    "bufsize": 0,
}
```

POSIX adds `start_new_session=True`.
Windows adds `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` and immediately assigns the process to a Job Object configured with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. If Job creation/configuration/assignment fails, terminate/reap the child and raise; never continue unowned. Keep the job handle open until cleanup. On normal root exit, close/terminate the job so descendants cannot outlive the operation. Do not call `taskkill` or invoke a shell.

Runtime-only handle shape:
```python
{
    "process": proc,
    "pid": proc.pid,
    "start_time": started_at_ns,
    "owner_request_id": owner_request_id,
    "tree": tree_owner,
    "readers": [stdout_reader, stderr_reader],
}
```

`start_time` is the operation-captured `time.time_ns()` ownership nonce. Cancellation acts on the retained process/job/group handle, never by unverified PID lookup. Return target `{pid,start_time}` as evidence.

`cancel(handle)`:
- Windows: terminate Job Object, wait root, close handle.
- POSIX: `os.killpg(pid, SIGTERM)`, wait up to grace, then SIGKILL if needed; reap root.
- Idempotent missing/exited groups are not errors.
- Return `{"tree_cleanup": bool, "exit_observed": bool}`.

`wait(handle)`:
- Wait root for timeout.
- On timeout, call `cancel`; return `{"timed_out": True, ...}`.
- On normal root exit, still close/terminate owned tree; return `{"timed_out": False, ...}`.
- Join both reader threads only after tree cleanup; bounded join and fail closed if EOF is not observed.

## Bounded output and spill

Each reader tracks:
- total bytes;
- a tail `bytearray` capped to `output_limit`;
- a complete owner-only temporary stream file only after overflow.

When overflow first occurs, write all bytes seen so far to the stream spill; continue streaming later chunks. Never buffer complete output in memory.

Final spill:
- no overflow: `evidence.spill = None`;
- one overflow: owner-only file containing that complete stream;
- both overflow: owner-only combined file with fixed ASCII section headers and complete stdout/stderr; remove intermediate files.

Result value:
```python
{
    "target": {"pid": int, "start_time": int},
    "owner_request_id": str,
    "exit_code": int | None,
    "started_at": float,
    "ended_at": float,
    "stdout": contract.untrusted(decoded_tail),
    "stderr": contract.untrusted(decoded_tail),
    "stdout_bytes": int,
    "stderr_bytes": int,
    "stdout_truncated": bool,
    "stderr_truncated": bool,
}
```

Decode tail with UTF-8 `errors="replace"`. `evidence.dropped` is total omitted inline bytes. Response:
- zero exit: `ok=True`, `status="dispatched"`;
- nonzero exit: `ok=False`, `status="unknown"`, error `process exited with code N`;
- timeout: `ok=False`, `status="timeout"`, error `process timed out`.

Always set:
```python
precondition={"argv_only": True, "cwd_verified": True,
              "environment_sanitized": True}
postcondition={"exit_observed": bool, "tree_cleanup": bool}
backend="subprocess"
```

## CLI

Add command `exec` with strict flags:
- required: `--argv-json`, `--request-id`, `--confirmation-id`;
- optional: `--cwd`, `--timeout`;
- no positional arguments, duplicates, or unknown flags.

Defaults: timeout `30`. Parse `--argv-json` as JSON, then apply spawn validation. Build this exact request before consuming confirmation:
```python
request = {
    "version": 1,
    "request_id": opts["request-id"],
    "capability": "process.exec",
    "args": {"argv": argv, "cwd": cwd, "timeout_s": timeout_s},
    "deadline_ms": max(1, int(timeout_s * 1000)),
    "policy": {"dry_run": False,
               "confirmation_id": opts["confirmation-id"]},
}
```

Flow:
1. `classify(request)` must return `confirm`.
2. `consume_confirmation(request, confirmation_id)` must return `ok=True`.
3. Only then call `sc_process.spawn`.
4. Overwrite result request_id with the supplied request ID and emit once.
5. Missing/mismatched/replayed/expired confirmation: `status:"rejected"`, exit 2.
6. Successful spawn result: exit 0 only when result `ok=True`; timeout/nonzero exits map to CLI exit 1.

Token issuance remains the generic Python policy API from Task 2; do not add another CLI command in this task.

## Visible tests

Write tests before implementation. Required coverage:

- Plan-prescribed tests: argv semicolon remains one argument and `shell=False`; output flood spills and keeps tail; timeout calls tree cleanup.
- Reject string/tuple/empty argv, empty/NUL elements.
- Reject invalid timeout/output/grace including bool/NaN/Infinity.
- Validate cwd and spill directory.
- Environment contains only baseline + explicit safe mapping.
- Secret-class keys reject before `Popen`; values never appear in result.
- stdout/stderr drain concurrently (child floods both beyond pipe capacity).
- Separate per-stream byte counts, tails, truncation, dropped count.
- Spill is complete and mode 0600 where supported.
- Nonzero exit maps unknown; zero maps dispatched; timeout maps timeout.
- External output is untrusted.
- Tree cleanup happens on success, nonzero, timeout, and reader failure.
- CLI rejects before spawn without confirmation.
- CLI exact-request confirmation succeeds once; replay and mutations of argv/cwd/timeout/request_id reject before spawn.
- CLI JSON remains exactly one stdout object and diagnostics stay stderr.

Use real subprocesses only for small Python integration cases. All children must be reaped by test teardown.

## Verification

RED:
`python -m pytest tests/test_sc_process_exec.py -q`
Expected failure on missing `spawn` behavior.

GREEN:
`python -m pytest tests/test_sc_process_exec.py tests/test_sc_policy.py tests/test_sc_cli.py -q`
Expected all pass.

Audit:
`python audit.py`
Expected exit 0, zero errors.

Full suite:
`python -m pytest -q`
Expected zero failures.

Report exact outputs and security self-review in `task-3-report.md`.

Reserved commit:
`feat(system-control): add bounded process execution`
