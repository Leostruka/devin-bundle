# Map: egm-laya-bitnet-upgrade

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Goldfish Review protocol + reviewer profiles | none | resolved (docs landed 2026-10-31) |
| 02 | `drift-audit` workflow design | 01 | resolved (design in `.devin/sdd/goldfish-review.md`) |
| 03 | LAYA §12 JEV patterns + MODEL-GUIDE BitNet/TPU section | none | resolved (docs landed 2026-10-31) |
| 04 | OpenUI Lang DSL spec (`.devin/rts/openui-lang.md`) | none | resolved (doc landed 2026-10-31) |
| 05 | Katana camera-blocking roadmap (blender + media-tools) | none | resolved (roadmaps landed 2026-10-31) |
| 06 | Drift cleanup Phase 3 (ADR 002, CONTEXT, README, maps) | none | resolved |

Frontier: all doc/roadmap tickets resolved. Implementation tickets for JEV
patterns (profile.json `eval_floor`, skill picker hook, two-stage explore
wiring) remain future work per LAYA §10.

## Ordering

Wave 1: docs + roadmaps (01-05, landed).
Wave 2: JEV-1..JEV-6 implementation tickets, gated on `layad` lifecycle per
LAYA §10 sequence; craft-bridge DSL op after `.devin/rts/openui-lang.md`.
