# Craft Anything - eval note

Source reel: noxprojectsx DfXQwlbz13S (reels batch-5 survey,
`.devin/research/2026-11-07-reels-batch5-survey.md`). Evaluated
2026-11-07.

## What it is

`github.com/storytold/craft-anything` - early-alpha (v0.5.0, created
2026-10-31), dual MIT/Apache-2.0, pure Rust. Pipeline: paste a URL ->
Study (inspection tools gather evidence) -> Build (spawns local
`claude -p` headless with its own MCP server + permission gates) ->
Check (compares render vs original at 3 widths, refines). ~280-320
inspection tools exposed as CLI + MCP. Vendor: ArtCraft community
(craftanything.lol). Requires Claude Code installed; uses your sign-in.

Reel claim verified: "clone/recreate the app and verify against the
original" matches the Study->Build->Check loop. Stars ~19-20k at eval
time (reel implied scale; treat as approximate).

## Maturity risks

- v0.5.0 alpha; clone fidelity unproven outside demo sites.
- Hard dependency on local Claude Code + user credentials - not
  model-agnostic; conflicts with free-model policy if used for routing.
- "Verification" is render-diff at 3 widths, not behavioral equivalence.

## Bundle fit

Adjacent, not duplicative: `extensions/rea-ops` + `skills/re-binary`
cover binary RE (REA, ~430k stars, already integrated); craft-anything
targets web/app cloning - different domain. `skills/cli-adapter` covers
the "no MCP -> build CLI" pattern craft-anything relies on.

## Recommendation

**Track, do not adopt.** Watch for v1.0 and independent fidelity
benchmarks. If a clone-app need materializes, pilot in a sandbox repo;
never route bundle work through it (credential + alpha risk).
