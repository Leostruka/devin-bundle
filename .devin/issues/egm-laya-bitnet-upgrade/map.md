# Map: egm-laya-bitnet-upgrade

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Goldfish Review protocol + reviewer profiles | none | resolved (docs landed 2026-10-31; gate/coverage wiring documented) |
| 02 | `drift-audit` workflow design | 01 | resolved (design in `.devin/sdd/goldfish-review.md`; reuses `skills/drift-report/`) |
| 03 | LAYA §12 JEV patterns + MODEL-GUIDE BitNet/TPU section | none | resolved (runtime lanes implemented; docs aligned to disk) |
| 04 | OpenUI Lang DSL spec (`.devin/rts/openui-lang.md`) | none | resolved (spec + `craft-bridge/ui_dsl.py` v1 implemented) |
| 05 | Katana camera-blocking roadmap (blender + media-tools) | none | resolved (camera_blocking.py + playblast_ingest.py implemented) |
| 06 | Drift cleanup Phase 3 (ADR 002, CONTEXT, README, maps) | none | resolved |

Frontier: JEV runtime lanes exist on disk (`compact-gate`, `skill-picker`,
`explore`, `review_gate`, `doc_coverage`, `cu_dom_picker`) and the doc
contract map shipped (`.devin/validation-contracts.json`, 11 tests in
`tests/validation/test_jev_runtime_contracts.py`). Remaining work is
adoption, not implementation: `profile.json` mode `off` -> calibration
(G5) before `shadow`/`assist`; `review-risk-v1` not yet in `profiles`;
no external Katana/Seedance or spark-view integration; no TPU hardware
verified; BitNet model quality not established (real `ok:true` run in
`devin-cache/egm-runtime-install/cli_proof2.json` produced a wrong
semantic completion).

## Ordering

Wave 1: docs + roadmaps (01-06, landed).
Wave 2 (landed): issue 04 JEV-1..JEV-6 runtime lanes; issue 02 DSL
parser/renderer + fixture benchmark (ratio 0.5654, target not met) +
relocated browser smoke; issue 03 camera pipeline + smoke
(`.devin/scratch/egm-smoke-controller/`, earlier `egm-smoke-l4/`
historical); issue 01 Goldfish protocol + drift-report reuse (unchanged;
no duplicate scanner).
Issue filenames 01-04 are grouped workstreams rather than a one-to-one
mapping to the table above.
