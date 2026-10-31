# egm-laya-bitnet-upgrade (spec)

## Intent

Land four workstreams from the 2026-10-31 source ingestion: (a) EGM Goldfish
Review protocol plus `drift-audit`, (b) JEV operational patterns in Laya,
(c) OpenUI Lang style line-based DSL for streamed HUDs and interactive
grilling forms in `craft-bridge`/`.devin/rts/`, (d) Higgsfield Katana style
camera-blocking export for `blender-operator`/`media-tools`. Doc-level
updates to `LAYA_MASTER_ARCHITECTURE.md` §12 and `MODEL-GUIDE.md` are already
landed this session; this spec covers the remaining build work.

## Problem Statement

- Spec review today embeds the implementer's rationale in context, anchoring
  the reviewer. No `zoom-out` first check exists as an enforced step.
- No `drift-audit` command exists; doc-vs-disk divergences are found by hand.
- The proposed line-based DSL targets half the tokens of equivalent JSON.
  This is an acceptance target, not a measured saving.
- Video pipelines (Katana / Seedance) need controlled camera blocking;
  `blender-operator` has no low-poly blocking or playblast export path.

## Solution

Vertical tickets, each gated. Protocol and DSL design land first; anything
touching `extensions/` keeps the stdlib-only / fail-closed invariants and
ships behind flags.

## User Stories

1. As the orchestrator, I want Goldfish review dispatches, so that spec reviews are unanchored and cheaper.
2. As the maintainer, I want `drift-audit` output, so that stale docs surface as a table instead of silent rot.
3. As the agent, I want a line-based UI DSL, so that streamed HUDs/forms cost half the tokens of nested JSON.
4. As the media pipeline, I want camera-blocking playblasts with metadata, so that Katana-style video gen gets precise camera intent.
5. As the Laya operator, I want the JEV patterns implemented per §12, so that compaction, skill picking, explore, and review triage stay cheap.

## Estimated size (lines)

~450-650 across 6 tickets; each ticket <= ~200.

## Input / Output boundaries

- Goldfish dispatch: brief file (`spec.md` path + diff command) -> reviewer
  subagent -> verdict block per `.devin/sdd/goldfish-review.md`.
- `drift-audit`: doc claims -> `.devin/notes/drift-report-<date>.md` table;
  read-only.
- OpenUI Lang: `.devin/rts/openui-lang.md` grammar + `craft-bridge` renderer
  op (`ops_map.json` entry) emitting line DSL; JSON path stays default.
- Katana blocking: `blender-operator` low-poly scene + camera track ->
  playblast MP4 + `camera.json` metadata -> `media-tools` handoff.

## Implementation Decisions

- Living: `.devin/sdd/goldfish-review.md` (landed), `drift-audit` spec +
  reporter script proposal, `.devin/rts/openui-lang.md`, craft-bridge DSL op,
  blender blocking helper, media-tools handoff note.
- Disposable: drift reports under `.devin/notes/`, playblast outputs in temp.
- No new deps for `scripts/`; craft-bridge/blender extensions may declare
  their own pinned deps as today.

## Testing Decisions

- `tests/validation/` contract tests: goldfish-review.md exists and is
  referenced by both reviewer profiles; ops_map.json validates; DSL grammar
  has a round-trip fixture; drift-audit reporter is pure function over a
  fixture tree.

## Out of Scope

EGM repo installation, BitNet integration into hooks or daemon, TPU job
automation, any credentialed scraping, changes to `hooks.v1.json` matchers.
