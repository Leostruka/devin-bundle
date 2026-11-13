# Task 4 report — persistent owned sessions

## Result
- `extensions/system-control/sc_sessions.py` (new, ~700 lines): loopback
  JSONL daemon + client surface.
- `extensions/system-control/sc_cli.py` (+~200): `sessions`/`session`
  commands, confirmation-gated mutations.
- `tests/test_sc_sessions.py` (21 tests) + `tests/test_sc_session_daemon.py`
  (16 tests): 37 green.
- Held-out `test_daemon_recovery.py` (lead-owned): 4 green.

## Design
- Pidfile `{pid, port, generation, daemon_token, started}` via
  `mkstemp`+`chmod 0600`+`os.replace`.
- Envelope `{daemon_token, generation, op, arg}`; foreign token/generation
  rejected before dispatch (`hmac.compare_digest`); only token-less `ping`.
- Client-side generation pre-check: session dict generation vs live pidfile
  — mismatch → `rejected`, no socket opened (prevents foreign-port sends).
- Per-session token + monotonic `seq` cursor ring buffer (default 2048
  records); `dropped` counted on eviction; `recv` supports
  cursor/limit/tail/regex-wait/timeout.
- Children bound to Job Objects (`sc_process._assign_tree`,
  KILL_ON_JOB_CLOSE): daemon hard-kill reaps every child (held-out
  verified via `taskkill /F`).
- Idle TTL reaps running sessions; `_EXITED_TTL_S=60` reaps exited ones.
- Absolute 30s request deadline; send payload capped 64KB; daemon-side
  capacity/idle_ttl strict-validated.

## Review history
- Round 1: spec/standards FAIL → 1 blocker (live-pidfile respawn
  orphaning sessions), 4 majors (stop_daemon unreachable orphan, no
  absolute request deadline, 1MB blocking send wedge, world-readable
  token files), 6 minors — all fixed in rework round.
- Round 2: rework verified by tests: live-pid ping-timeout no-respawn,
  oversized send, bad capacity/ttl rejection, atomic pidfile roundtrip,
  stale-generation rejected without socket dispatch.

## Evidence
- `pytest tests/test_sc_sessions.py tests/test_sc_session_daemon.py -q`:
  37 passed.
- Held-out: `pytest tests/held-out/system-control/test_daemon_recovery.py`:
  4 passed.
- Slice: 169 passed (held-out T5/T6 skip pending implementation).
- Full suite: 749 passed, 12 skipped (1 pre-existing `cu_screenshot` +
  11 pending held-out T5/T6).
- `python audit.py`: 0 errors, 1 pre-existing `__pycache__` warning.

## Residual
- POSIX: no parent-death binding — `kill -9` daemon leaves orphans
  (finalizer covers graceful exit only). Windows safe via Job Objects.
- `send` blocking write bounded only by socket timeouts (payload ≤64KB).
- Pidfile/session tokens plaintext in `%TEMP%` — per-user ACL only.
- `recv` record = one pipe read, not a line.
- Single-threaded accept loop: a 60s `recv --wait` blocks other ops
  (documented; a threaded dispatcher is a T11 candidate).
