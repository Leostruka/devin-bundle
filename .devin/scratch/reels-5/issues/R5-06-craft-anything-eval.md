# research note: craft-anything eval (clone-app pipeline)

status: ready-for-agent
priority: P3
source: reels batch-5 survey, noxprojectsx DfXQwlbz13S

## Evidence

Transcript (`.devin/scratch/reels-5/transcripts/DfXQwlbz13S.txt`): reel contrasts REA ("reverse engineer anything", ~430k stars, verified `github.com/morluto/rea`, already integrated via `extensions/rea-ops` + `skills/re-binary`) with "Craft Anything": paste a link, press Start, it clones/recreates the app and verifies the result against the original.

Verified identity: `github.com/storytold/craft-anything`, ~19-20k stars, created 2026-10-31, v0.5.0 early alpha, dual MIT/Apache-2.0, pure Rust. Pipeline: Study (inspection tools gather evidence) -> Build (spawns local `claude -p` headless with its own MCP server + permission gates) -> Check (compares render vs original at 3 widths, refines). ~280-320 inspection tools exposed as CLI + MCP. Vendor: ArtCraft community (craftanything.lol). Requires Claude Code installed; uses your sign-in.

Bundle adjacency: `skills/cli-adapter` (agent builds CLI when no MCP), `extensions/rea-ops`, `skills/re-binary` (binary RE, different domain: craft-anything targets web/apps, not binaries). Alpha quality unverified.

## Task

Write an eval note at `.devin/research/craft-anything-eval.md` (follow the format of prior eval notes like `heyclicky-eval.md`/`opendots-map.md`): what it is, verified facts vs reel claims, maturity risks, bundle fit (candidate future extension vs covered-by-existing), recommendation (track / pilot / reject). Check `.devin/research/INDEX.md` and add a row if the index catalogs evals.

## Acceptance

- [ ] Eval note exists with verified repo facts (stars/license/activity dated)
- [ ] Explicit adopt/track/reject recommendation with rationale
- [ ] INDEX.md updated if applicable
