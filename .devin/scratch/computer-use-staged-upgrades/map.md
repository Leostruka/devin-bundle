# Map — computer-use-staged-upgrades

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Measurement harness + baseline | — | resolved |
| 02 | Capture seam `cu_capture` (MSS) | — | resolved |
| 03 | Move/dirty-rect reconstruction | 02 | resolved |
| 04 | Browser binding contract `cu_browser` | — | resolved |
| 05 | Adversarial fixtures + workflows | — | resolved |
| 06 | DXcam/WGC adapter | 01, 02, 03 | resolved — not adopted |
| 07 | Persistent session worker | 01 | resolved |
| 08 | Comparative report | 05, 06, 07 | resolved |
| 09 | Browser action routing (`--via browser`) | — | resolved |
| 10 | Actionability check | 09 | resolved |
| 11 | iframe/shadow context scoping | 09 | resolved |
| 12 | Canvas/graphics visual fallback | 09 | resolved |
| 13 | Session worker opt-in wiring | — | resolved |
| 14 | Held-out/validation test split | — | resolved |
| 15 | Missing adversarial cases | 14 | resolved |
| 16 | Concurrent snapshot writes | — | resolved |
| 17 | UIA round-trip measurement | — | resolved |

Frontier: none — all 17 tickets resolved.

## Ordering (topological + risk-first)

Wave 1 (no blockers): 09 → unlocks 10/11/12; 13; 14 → unlocks 15; 16; 17
Wave 2: 10, 11, 12 (after 09); 15 (after 14)

Tie-break rule: correctness-risk first (routing/contexts), then
evidence/tests (14/15/16), then measurement (17).
