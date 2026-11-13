# Reels batch-5 execution plan (2026-11-07)

Inputs: 11 Instagram links (3 batch-4 overlap). Survey: `.devin/research/2026-11-07-reels-batch5-survey.md`.
Issues: `.devin/scratch/reels-5/issues/R5-01..08`.
Parallel workstream: adequacao Devin CLI 3000.11.234 -> 3000.12.17 (installed `d23bb600ed8f`).

## Wave 1 (P2)
- R5-01 dep-audit: `scripts/dep-audit.py` + `scripts/dep-audit-gate.py` + hooks.v1.json PostToolUse + security-audit pointer + tests
- R5-02 upload-trust: `skills/frontend-design/SKILL.md` upload/file-state checklist

## Wave 2 (P3 docs/evals)
- R5-03 style-taxonomy ref (design-intelligence/frontend-design pointer)
- R5-04 dashboard-reflow note (frontend-design; verify moxen.cl/recursos/parrilla first)
- R5-05 airesearches sources (verify airesearches.tech/feed; record RSS/archive candidates)
- R5-06 craft-anything eval note (.devin/research/)
- R5-07 wici-one + inferssd eval note (.devin/research/)
- R5-08 SLEEP pointer (doc-only cross-link)

## Parallel: CLI 3000.12.17 adequacy
- `data/bundle-identity.json` bump + README + `.devin/docs/DEVIN-CLI-COMPATIBILITY.md` new section (changelog delta 3000.11.234->3000.12.17: /vim, model pinning, permission_mode config, `devin mcp list --json`, ContextInput hooks, PostToolUse truncated-output path, UserPromptSubmit-on-handoff) + TOOLS-MAP sync + CHANGELOG.

## Per wave
manifest hashes -> audit -> tests -> branch -> changelog -> push -> PR -> merge -> install -Force -> doctor -> remote align. Site rebuild when public-facing files change.
