# 53 -- No ADR for hook consolidation into aggregator scripts

- **Status**: open
- **Category**: adr
- **Severity**: P2
- **File**: scripts/pre-exec-guard.py

## Evidence
At some point the bundle moved from ~21 individually bound hook commands
(the layout still documented in TOOLS-MAP, issue 46) to 10 aggregator
entry points that spawn inner scripts through `_hookrun.py`. That is a
significant architecture decision: it trades per-script timeouts and
matchers for one process spawn per event, changes failure semantics
(inner fail-open vs entry `fail_closed: true`), and changed the
`hooks.v1.json` schema of record. No ADR covers the motivation
(presumably spawn-cost on every tool call), the alternatives (matcher
broadening, a single omnibus guard), or the invariants inner scripts
must now satisfy (stdin contract, stdout JSON merge).

## Recommendation
Add `.devin/adr/NNN-hook-consolidation.md` capturing the spawn-cost
rationale, merge semantics pointer to `_hookrun.py`, and the rule that
inner scripts must never be bound directly in hooks.v1.json.

## Tradeoffs
Consolidation makes per-script latency invisible to the CLI timeout
budget; an ADR should record the measured savings if any exist.

## Verification
ADR exists and is referenced from ARCHITECTURE_MANIFEST.md hook section.
