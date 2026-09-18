# 16 — Concurrent snapshot writes

**Intent:** two simultaneous captures must not produce torn sidecar JSON;
last-writer-wins deterministically.

**What to build:** threaded test writing two sidecars concurrently +
mid-write kill simulation (write tmp, never replace) -> reader sees old
valid JSON or none, never partial. If the atomic tmp+replace contract
already guarantees it, the test proves it.

**Proposed modules:** `tests/test_cu_observation_contract.py` (+case).

**Estimated size (lines):** ~60 tests

**Input / Output:** concurrent writers -> parseable final sidecar

**Blocked by:** none

**Gate:** `python -m pytest tests/test_cu_observation_contract.py -q`

**Expect:** exit 0; final file parses, one generation wins

**Evidence:** pytest output

**Status:** resolved

- [ ] no torn JSON under concurrent write
- [ ] interrupted write leaves previous intact

## Answer

Fixture caught a REAL race: shared `.tmp` path + non-atomic generation read
-> PermissionError/duplicate gens on Windows. Fixed with module-level
`_SIDECAR_LOCK` serializing read+write+replace. Evidence: 13/13.
