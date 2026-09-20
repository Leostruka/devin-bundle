# Task 5 brief — bounded, resumable event streams

Lead notes:
- Worktree: `D:\Programing\ai_workspace\devin-bundle-system-control`, branch `feat/system-control`.
- Follow `.devin/plans/2026-09-19-system-control.md` Task 5.
- Do not read or modify `tests/held-out/`; do not commit/PR/push.

Create `extensions/system-control/sc_telemetry.py`: normalized event
envelopes + bounded stream registry + reducer. Streams must persist
across CLI invocations → host them inside the existing `sc_sessions`
daemon (extend its `_op` dispatch with stream ops; reuse its
generation/token auth). stdlib only; target ~450 lines telemetry +
~120 daemon/CLI additions.

## Pure API (`sc_telemetry`) — in-process, unit-testable

- `normalize(subject, *, source, kind, severity="info", ts=None,
  attrs=None) -> event dict`
  - Event fields: `ts` (event time, default now), `observed_ts` (always
    now), `source`, `kind`, `subject` (dict, e.g. `{"pid":7,
    "start_time":9}`), `severity` (info|warning|error), `attrs` (dict),
    `cursor` (int, from a module-level monotonic counter — NEVER from
    `ts`; a reversed `ts` must still yield a larger cursor than a prior
    normalize call), `dropped` (0).
  - `attrs` is untrusted: redact values whose key matches secret shapes
    (`password|passwd|token|secret|api[_-]?key|authorization|cookie|
    credential|private[_-]?key`, case-insensitive, substring match on
    key) → `"***"`. Non-dict attrs → `{}`. Cap attrs at 32 keys and
    values at 512 chars (truncate with marker).
- `open_stream(*, capacity=1024, ttl_s=300, provider=None,
  interval_s=5.0) -> {"ok": True, "stream": stream_obj}`
  - `stream_obj`: has `.id` (uuid hex), `.feed(iterable_of_events)`,
    and lives in a module registry keyed by id.
  - `provider`: optional zero-arg callable polled by `drain` (and by a
    daemon-side poller). Provider exceptions must surface as a
    structured `{"ok": False}` drain result — never propagate.
  - `feed` appends to `deque(maxlen=capacity)`; eviction increments
    `dropped`; stream records `base_seq`/`next_seq`.
- `drain(stream_id_or_obj, *, cursor=None, limit=100)`
  → result envelope: `{"ok": True, "status": "verified",
  "value": {"events": [...], "cursor": last_seq,
  "resync_required": bool}, "evidence": {"dropped": n,
  "spill": None}}`.
  - `cursor < base_seq` → `resync_required: True`, return retained
    window — never silently skip.
  - Unknown/closed stream → `{"ok": False, "status": "rejected"}`.
  - Provider failure → `{"ok": False, "status": "unknown",
    "error": ...}`.
- `close_stream(stream_id)` → removes from registry; later ops rejected.
- `reduce_events(events, *, top_k=10)` → `{"groups": [{kind, subject,
  count, first_ts, last_ts, sample}...], "errors": [...], "dropped": n,
  "total": n}` — group by (kind, subject-json); errors preserved in
  `errors` list (severity=error or kind containing "error"/"overflow");
  `dropped` aggregates event `dropped` fields.
- Stream TTL: `expired` streams auto-reject drain (treat as closed).

## Provider: process snapshot diff (all backends)

Add to each `backends/{windows,linux,macos}.py`:
`process_event_provider()` returning a zero-arg callable. Each call
diffs `process_list()` against the previous snapshot (closure state)
and yields normalized `process.start` / `process.exit` events with
`subject={"pid","start_time"}`, `attrs={"name": ...}`, source=backend
name. First call emits nothing (baseline). Snapshot failures yield a
single `{"kind": "provider.error", "severity": "error"}` event — never
raise. Advertise `mode: "poll"`, `events.process` capability in
`capabilities()` (supported=True when process.observe is).

## Daemon hosting (`sc_sessions.py`)

Extend `_op` with: `stream.open {capacity?,ttl_s?,provider?,
interval_s?}` | `stream.drain {id,cursor?,limit?}` |
`stream.close {id}` | `stream.list`. Streams keyed by id inside the
daemon; same envelope auth (daemon_token+generation). A daemon-side
poller thread per provider-stream ticks `provider()` at `interval_s`
(clamped ≥1s) into `feed`; poller dies with stream close/TTL/daemon
finalizer. `provider:"process"` maps to the backend provider; any other
string → rejected. No-op providers allowed (feed-only streams).

## Client + CLI (`sc_cli.py`)

Client wrappers in `sc_telemetry`: `open_stream_remote`,
`drain_remote`, `close_stream_remote`, `list_streams_remote` — envelope
via `sc_sessions._authed` pidfile path (no session dict needed; add an
optional param or small `_authed_op` helper if cleaner).

CLI: `events open [--kind process] [--capacity N] [--ttl S]
[--interval S]` | `events drain --stream-id ID [--cursor N]
[--limit N]` | `events close --stream-id ID` | `events list`.
Capabilities `events.open|drain|close` are ALLOW — no confirmation.
Missing/unknown stream-id → rejected, exit 2.

## Visible tests (RED first)

`tests/test_sc_telemetry.py` + `tests/test_sc_event_streams.py`:
normalize shape/monotonic cursor/secret redaction/attr caps; feed
overflow → dropped; drain bounded + resync; closed/unknown rejection;
provider error structured; reducer grouping/errors/dropped; TTL expiry;
backend provider first-call-baseline then diff events (fake
process_list monkeypatch); daemon-hosted open→drain→close roundtrip via
`start_daemon()` (monkeypatch PIDFILE like T4 tests); CLI arg
validation. Keep tests fast — use `interval_s` small only where needed;
no fixed sleeps, poll with deadline.

## Gates

- `python -m pytest tests/test_sc_telemetry.py tests/test_sc_event_streams.py -q` → 0 fails.
- `python -m pytest tests/test_sc_sessions.py tests/test_sc_session_daemon.py tests/test_sc_cli.py -q` → no regression.
- `python -m py_compile` on all touched files.

Report: files+lines, API signatures, test names/counts, residuals.
