# Task 5 report — bounded resumable event streams

## Result
- `extensions/system-control/sc_telemetry.py` (new, ~290): normalize,
  stream registry, drain, close, reduce, remote wrappers.
- `backends/__init__.py` + `{windows,linux,macos}.py`:
  `process_event_provider()` snapshot-diff (start/exit events,
  `mode:"poll"`, locked shared state).
- `sc_sessions.py` (+~130): `stream.open|drain|close|list` ops under the
  same envelope auth; poller thread per provider stream; stream reaper.
- `sc_cli.py` (+~75): `events open|drain|close|list` — all ALLOW.
- Tests: `test_sc_telemetry.py` 17 + `test_sc_event_streams.py` 10 = 27.

## Design
- Global monotonic cursor (`itertools.count`+lock) independent of `ts`.
- Secret redaction: key substring match (case-insensitive) + non-scalar
  values → `"***"` (nested dicts never serialized).
- Ring `deque(maxlen)` + `dropped`; `cursor < base_seq` →
  `resync_required: true` + retained window, never silent-skip.
- Daemon-hosted streams (`hosted` flag): poller thread feeds buffer;
  `drain` never polls inline → no PowerShell on the accept loop.
- Provider state locked; provider failures → `provider.error` event or
  structured `{"ok": False, "status": "unknown"}`.
- Strict numeric validation (bools/NaN/inf rejected) for
  capacity/ttl/interval.

## Review history
- Round 1: Spec PASS / Standards FAIL — double-poll race on shared
  provider state + accept-loop stall; nested-attr secret leak; NaN ttl;
  missing `events.list` policy entry; unguarded drain id; orphan window
  on poller start failure; test daemon leak; non-dict feed.
- Rework: all closed; hosted-flag split verified by call-count spy test.

## Evidence
- `pytest tests/test_sc_telemetry.py tests/test_sc_event_streams.py
  tests/test_sc_sessions.py tests/test_sc_session_daemon.py
  tests/test_sc_cli.py` + held-out: 108 passed.
- Held-out `test_event_integrity.py`: 6/6 first-try.
- Full suite: 782 passed, 6 skipped (1 `cu_screenshot` + 5 pending
  T6 held-out).
- `python audit.py`: 0 errors, 1 pre-existing `__pycache__` warning.

## Residual
- In-process expired streams stay in `_REGISTRY` (drain rejects; reaped
  lazily by daemon ops only).
- Process events are snapshot-diff polls (≥1s interval) — no WMI
  subscription/ETW yet; `mode:"poll"` advertised. T7 may add native.
- Feed-only streams opened via daemon can't be fed remotely (no push op).
