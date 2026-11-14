# 13 — Session worker opt-in wiring ($CU_SESSION)

**Intent:** amortize the measured ~142ms startup when explicitly enabled;
default path untouched.

**What to build:** `$CU_SESSION=1` -> frontends route commands through a
cu_session.Worker running a worker entrypoint (mouse/type/screenshot ops
as JSON commands); worker exits on session TTL or stdin EOF; cleanup
releases OwnedInputs; result keeps the one-JSON-stdout contract.

**Proposed modules:** `cu_session.py` (+worker entrypoint), thin dispatch
shim in `mouse.py`/`type_text.py`/`screenshot.py`.

**Estimated size (lines):** ~140 + ~80 tests

**Input / Output:** same CLI args -> same JSON schema; env decides transport

**Blocked by:** none (07 landed)

**Gate:** `python -m pytest tests/test_cu_session_isolation.py -q` +
`CU_SESSION=1 screenshot.py` dry-run in venv

**Expect:** identical JSON contract via worker; worker dies on EOF;
baseline startup amortization measurable in cu_bench rerun

**Evidence:** pytest + bench diff JSON

**Status:** resolved

- [ ] default path unchanged without env
- [ ] worker death -> clean error, no zombie input state
- [ ] bench shows startup amortized over N calls

## Answer

`--daemon` loopback listener (127.0.0.1, idle-TTL, pidfile in temp) +
`cu_session_dispatch.run_via_daemon`; `CU_SESSION=1` shim in mouse/type/
screenshot. Found+fixed re-entrant deadlock (daemon inherited CU_SESSION).
Honest gain: ~150ms vs ~183ms direct — caller still pays interpreter startup;
real amortization needs a long-lived caller. Evidence: live roundtrip ok.
