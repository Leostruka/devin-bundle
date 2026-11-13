# audit-r2 -- round 2 map

Scope: laya-compactor internals (transcript pairing, pair actions,
reduction accounting, CLI error surface) -- areas not covered by the
general audit and R1.

| # | Issue | Priority | Status | Gate |
|---|-------|----------|--------|------|
| 01 | tool_result sem tool_use_id pareava com tool_use sem id | P2 | resolved | tests/test_laya_compactor.py |
| 02 | chars desatualizados apos truncate distorciam reduction | P2 | resolved | tests/test_laya_compactor.py |
| 03 | falhas de IO/JSON no main() saiam como traceback | P3 | resolved | tests/test_laya_compactor.py |

Falsos positivos descartados: decision_client existe (import valido);
filebool zip paridade garantida por lc.batch; agent-reach whitelist
ja rejeita canais com credencial e flags.
