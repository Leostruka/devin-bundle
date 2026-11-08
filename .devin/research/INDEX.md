# Research index

Maps bundle subsystems to their originating research/plan artifacts so a
reader can reach the "why" behind a subsystem in <=2 hops from
CHANGELOG.md or `manifest.json`. Add a row whenever a subsystem lands or
a research doc spawns one.

| Subsystem | Origin artifacts |
|---|---|
| laya-guard / compact-gate (compaction triggers, layers 4+7) | `.devin/research/LAYA_MASTER_ARCHITECTURE.md` |
| thermos / thermo-nuclear review lanes | vendored, see `.devin/adr/008-vendored-skill-policy.md` and `manifest.json` source fields |
| de-slop / unslop / lean-code / no-comments quality wave | CHANGELOG [Unreleased] #295; `manifest.json` source fields |
| computer-use extension | `.devin/research/cu-*.md`, `cu-benchmark-baseline.json` |
| system-control extension | `.devin/research/swe2-full-system-control.md`, `system-control-benchmark.json`, `virtual-input-devices*.md`, `sandboxie-isolation-*.md`, `host-input-routing.md` |
| scrape-tools extension | `.devin/research/scrapling-integration.md` |
| memory pipeline | `.devin/docs/MEMORY-PIPELINE.md` (evidence: arXiv:2607.20972, 2608.15008) |
| hook consolidation | `.devin/adr/006-hook-consolidation.md`, `.devin/docs/HOOKS-PIPELINE.md` |
| install drift ledger | `.devin/docs/DRIFT-LEDGER.md`, `.devin/issues/MILESTONE_2_06_install_drift_ledger.md` |
| skill/model routing registry | `data/bundle-models.json`, `.devin/docs/MODEL-GUIDE.md`, `.devin/adr/002-subagent-model-swe-1-7.md` (superseded) |
| media/3d extensions | `.devin/research/3d-tools-comparison.md`, `pocock_port_matrix.md`, `rizin-*.md` |
| red-team / security skills | `.devin/research/red-team-domains.md` |
| spec-driven development flow | `.devin/research/spec-driven-development.md` |
| reels-batch evals & external-tool notes | `.devin/research/heyclicky-eval.md`, `craft-anything-eval.md`, `wici-one-eval.md`, `2026-11-0*-reels-batch*-survey.md` |
| milestone planning (M2_*) | `.devin/research/MILESTONE_NEXTGEN_MATRIX.md`, `.devin/research/bundle-capability-map.md` |
| ISSUE_01-07 epic origins | `.devin/research/4_fronts_recon.md` |
| office specialists wave (M2_15) | `.devin/research/2026-11-07-office-gap-analysis.md` |
| agent-desktop computer-use backend | `.devin/research/2026-11-09-agent-desktop-eval.md` -> `extensions/computer-use/cu_agent_desktop.py` |
| yt-batch1 video survey + evals | `.devin/research/2026-11-09-yt-batch1-survey.md` -> issues #423-#426 |
| external evals (track decisions) | `.devin/research/2026-11-08-roon-eval.md`, `2026-11-08-mirofish-eval.md`, `2026-11-09-stageshow-eval.md`, `2026-11-09-dropstone-eval.md`, `2026-11-09-pr-agent-eval.md` |
| dated survey/eval notes (context, no subsystem) | `2026-11-0*-reels-batch*-survey.md`, `2026-11-03-*-survey.md`, `2026-11-03-meridian-altdata-backlog.md`, `2026-11-03-pstack-backlog-eval.md`, `2026-11-05-r*-evals.md` |
