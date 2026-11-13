# Eval: stageshow skill (issue #424) - 2026-11-09

Source video: youtu.be/of628n5754g (AI LABS).
Real artifact: `benjitaylor/skills` repo, skill `stageshow` v1.1.1 -
Benji Taylor, Head of Design at X/SpaceXAI (verified: benji.org,
@benjitaylor, joined X 2026-03). Released 2026-10-31, ~2.6k stars.
Install: `npx skills add benjitaylor/skills --skill stageshow`.

## What it is

SKILL.md-format skill for **faux UI**: believable miniature product
interfaces as stills or short animations (cursor walkthroughs, bento
grids, dashboards, phones, terminals) for landing pages, feature cards,
docs heroes, promo motion. React/CSS kit + scripts (`film.mjs`,
`jumps.mjs`, `layout.mjs`) that render frames and programmatically gate
every frame (width, loop seam). Explicitly "authored illustrations, not
browser automation".

Structure worth noting:
- **7-step workflow** decided before code: medium/place → look (design
  tokens) → story (3-5 beats, 10-16s) → start-from-gold-example → screen
  (3-7 real strings budget) → choreograph (Act API) → rehearse.
- **Gold examples**: `examples/` folder of gold-standard demos; new work
  copies the closest gold then replaces look/content - a concrete
  few-shot pattern inside the skill.
- **Rehearsal gate**: `film.mjs --gate` prints per-frame faults; handover
  requires `rehearsal passed` + fresh-eye review + `REHEARSAL.md` artifact
  (template in references/verify.md).
- Failure catalog: too-much / wireframe / boxed / flat / bland - each
  with its fix rule. Craft references: restraint, framing, motion,
  rehearse, review, teaching.

## Fit with devin-bundle

- Adjacent, not overlapping: `animation-direction` = narration→Remotion
  explainer; `media-tools`/`design-intelligence` = asset pipelines.
  stageshow covers **marketing-product-UI mockups** - an artifact class
  we don't produce today.
- **License: none** (repo has no LICENSE - all rights reserved).
  Cannot vendor into bundle; can only reference as external install.
- Portable patterns (license-free ideas):
  1. plan-first workflow with beats/payoff decided pre-code;
  2. gold-example copy-then-replace few-shot inside skill;
  3. **rehearsal gate** - deterministic per-frame fault checklist +
     mandatory REHEARSAL.md handover artifact. Our skills verify by
     tests; visual artifacts have no equivalent gate - this is the gap
     it fills conceptually.

## Recommendation

**TRACK + adopt the pattern, not the code.**
- Document stageshow in TOOLS-MAP as an optional external skill
  (`npx skills add benjitaylor/skills --skill stageshow`) for faux-UI
  work - no vendoring (no license).
- File follow-up: add a "rehearsal gate" section to `writing-skills`
  (or a visual-artifact verification note in animation-direction):
  for visual deliverables, define the deterministic frame/fault gate +
  handover artifact before building - same contract as our test gates.

## Evidence

- Repo: github.com/benjitaylor/skills (no LICENSE), SKILL.md v1.1.1
  fetched and read in full (7-step workflow, gold examples, --gate)
- Author: benji.org, X post 2026-10-31 (npx skills add command)
- Transcript: .devin/scratch/yt-batch1/transcripts/of628n5754g.json
