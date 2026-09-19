# Task 4 brief — persistent owned sessions

Lead notes:
- Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`, branch `feat/system-control`.
- Follow `.devin/plans/2026-09-19-system-control.md` Task 4.
- Do not read or modify `tests/held-out/`; do not run audit/PR/push.

Create `extensions/system-control/sc_sessions.py`: a session daemon holding
owned subprocesses across CLI invocations, plus client functions used by
`sc_cli.py`. Model on `extensions/computer-use/terminal_sessions.py` and the
Task 3 process machinery in `sc_process.py` (reuse `_assign_tree`,
`_reap_tree`, `validate_spawn`, reader pattern via import — same package).
stdlib only; target ~450 lines.

## Daemon

- Loopback socket `127.0.0.1:0`, JSONL one-request-per-connection (pattern
  from `terminal_sessions.daemon_main`), `socket.timeout` 1.0 accept loop.
- Pidfile `PIDFILE = %TEMP%/devin-sc-sessions.json`, atomic write via
  tmp+`os.replace`. Fields: `{pid, port, generation, daemon_token, started}`.
  `generation = uuid4().hex`, `daemon_token = secrets.token_hex(16)`.
- Envelope `{daemon_token, generation, op, arg}` — reject wrong/missing
  token or foreign generation `{"ok": False, "status": "rejected"}` **before**
  dispatching `_op`. Malformed JSON / oversized line (>1MB) → structured
  `{"ok": False, "error": ...}`, never crash the loop.
- Idle exit after `IDLE_TTL_S` (default 900, env `SC_SESSIONS_IDLE`
  overridable, `monkeypatch`-able module constant). Daemon finalizer
  (finally) cancels every live session tree and removes pidfile.
- Spawn detached like `sc_process`/`browser.py` daemon-start pattern:
  `DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP` on nt, `start_new_session`
  posix; poll pidfile up to ~5s.

## Client surface (module-level, used by tests and CLI)

- `start_daemon() -> {"ok", "daemon": {pid, port, generation}}` — no-op if a
  live daemon answers a token-less `ping`; a stale pidfile (dead pid or
  unreachable port) is removed and reported, never silently attached.
- `daemon_status() -> {"ok", "running": bool, "generation": str|None,
  "daemon": {...}|None, "sessions": int}`.
- `stop_daemon() -> {"ok": True}` (missing daemon → `{"ok": True,
  "running": False}`).
- `spawn_session(argv, *, cwd=None, capacity=2048, idle_ttl_s=900)`
  → `{"ok", "session": session_dict}`.
- `send(session, data)` → `{"ok", "delivered": int}` — `data` str only;
  empty or non-str rejected client-side.
- `recv(session, *, cursor=None, limit=200, tail=None, wait=None,
  timeout_s=10)` → `{"ok", "records": [...], "cursor": int,
  "dropped": int, "exited": bool, "exit_code": int|None}`.
  `wait` is a regex matched against newly arriving text within `timeout_s`.
- `resize(session, cols, rows)` → `{"ok": False, "error": "unsupported:
  session has no PTY"}` (pipe sessions; reserved for T7 adapters).
- `close(session)` → drain pending output then remove session, kill tree.
- `cancel(session)` → kill tree immediately, keep buffer until close.

All client functions take the `session` dict returned by `spawn_session`
(which carries `id`, `token`, `generation`, `daemon_token`, `pid`,
`start_time`, `argv`, `cwd`, `capacity`, `created_at`). Reject a session
dict missing required keys before socket IO.

## Session internals (daemon side)

- `subprocess.Popen(argv, stdin=PIPE, stdout=PIPE, stderr=STDOUT,
  bufsize=0, cwd=cwd, env=sanitized)` via `sc_process.validate_spawn`
  rules (argv list, no NUL, cwd strict dir). Assign to a Job Object
  (`sc_process._assign_tree`) so daemon death kills every child tree
  (held-out hard-kill test depends on this).
- Per-session random `token` (`secrets.token_hex(16)`); ops must match
  session id AND token AND live generation — else `status: "rejected"`,
  no dispatch.
- Ring buffer `collections.deque(maxlen=capacity)` of records
  `{"seq": int, "ts": float, "text": str}`; reader thread decodes utf-8
  errors=replace; eviction increments `dropped`.
- `seq` is the monotonic cursor; `recv(cursor=k)` returns records with
  `seq > k`; `tail=n` returns last n.
- Process exit recorded as final record flag `exited`; `send` to exited
  session → `{"ok": False, "error": "session exited"}`.
- `close`/`cancel` reap via `sc_process._reap_tree`; `close` removes the
  session (further ops rejected); `cancel` marks exited but keeps buffer.
- Idle `idle_ttl_s` per session reap in accept loop when no activity.

## CLI (`sc_cli.py`)

Add commands (request-envelope `_out` shape as existing commands; policy
classify + confirmation exactly like `exec`):

- `sessions start` → `daemon.start` (allow)
- `sessions status` → `daemon.status` (allow)
- `sessions list` → `session.status` for all live sessions (allow)
- `sessions stop` → `daemon.stop` (CONFIRM, `--confirmation-id`)
- `session spawn --confirmation-id ID [--cwd DIR] [--capacity N]
  [--idle-ttl S] -- ARGV...` → `session.spawn`
- `session send --confirmation-id ID --session-file F` or
  `--session-json JSON` + `--data TEXT` → `session.send`
- `session recv --session-file F [--cursor N] [--tail N] [--wait REGEX]
  [--timeout S]` → `session.recv`
- `session resize --session-file F --cols N --rows N` → `session.resize`
- `session close --session-file F` → `session.close`
- `session cancel --confirmation-id ID --session-file F` → `session.cancel`

`--session-file` reads the JSON session dict that `session spawn` wrote
(--out-file or stdout copy); `--session-json` accepts inline JSON.
Confirmation is consumed only after full arg validation (pattern from
`exec`). Unknown session file → rejected, exit 2.

## Visible tests (you write; RED first)

`tests/test_sc_sessions.py` + `tests/test_sc_session_daemon.py` covering:
spawn/echo roundtrip via send+recv; ring overflow reports `dropped`;
cursor paging; `wait` regex hit and timeout; `resize` unsupported;
`close` kills tree; `cancel` keeps buffer; stale session dict rejected;
malformed daemon message → structured error; daemon stop reaps children;
CLI arg validation (missing confirmation → rejected exit 2; bad session
file → exit 2). Use `tmp_path` PIDFILE monkeypatch like the held-out
fixture. Avoid fixed sleeps: poll for 'READY'.

## Gates

- `python -m pytest tests/test_sc_sessions.py tests/test_sc_session_daemon.py -q` → 0 fails.
- `python -m pytest tests/test_sc_process_exec.py tests/test_sc_policy.py tests/test_sc_cli.py -q` → 0 fails (no regression).
- Line target ~450 for `sc_sessions.py`; CLI additions <200.

Report: files changed, exact API signatures, residual limits (POSIX
parent-death, Windows ACL), line counts, test names.
