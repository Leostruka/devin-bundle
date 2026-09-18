# 07 — Persistent session worker `cu_session`

**Intent:** amortize interpreter/COM startup ONLY if 01 shows it dominates;
isolate hang-prone UIA in a recyclable worker. Not a security sandbox.

**What to build:** `extensions/computer-use/cu_session.py` — local worker per
session_id: loop over JSON-line commands on a local pipe/ACL'd endpoint;
single input executor; recyclable UIA subprocess; cancel() drains queue;
restart invalidates generation/session. Frontends keep one-JSON-per-call.
`tests/test_cu_session_isolation.py` with fake workers: session A can't use
B's hints, restart invalidates ids, hung provider killed+recreated, cancel
mid-gesture releases owned inputs, no public socket.

**Proposed modules:** new `cu_session.py`; touch frontends only behind
$CU_SESSION=1 opt-in.

**Estimated size (lines):** ~200 + ~140 tests

**Input / Output:** JSON-line commands in -> JSON results out; same contract fields

**Blocked by:** 01

**Gate:** `python -m pytest tests/test_cu_session_isolation.py -q`

**Expect:** exit 0; isolation invariants pass; loopback-only transport

**Evidence:** pytest output + 01 numbers cited in ticket comments

**Status:** resolved

- [x] opt-in only; default path unchanged
- [x] restart invalidates session/generation
- [x] no public network listener

## Answer

`cu_session.py` landed (opt-in): stdio-pipe worker, timeout->kill+respawn,
generation+session rotation, queue cancel. Fixed two real bugs found by the
gate (Queue.get positional arg; stale pump leaking into respawned queue).
Evidence: `test_cu_session_isolation.py` 9/9; startup 141.7ms baseline.
