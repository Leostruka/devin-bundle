# Eval: Dropstone (issue #425) - 2026-11-09

Source video: youtu.be/z5kcsAmoZRo (Epic Programmer, "I Cancelled Claude
Code"). Product verified real: dropstone.io + docs.dropstone.io.

## What it is

Terminal coding agent on **open-weight models only**. Three tiers are
slots, not models: Fast / Pro / Heavy, re-evaluated monthly.
Lineup 1.8 (in service): Fast=DeepSeek V4.1 Flash, Pro=GLM-5.3 Flash,
Heavy=Kimi K3. Lineup history public (1.5→1.8); models get promoted/
demoted between tiers (GLM-5.2 went Heavy→Pro). Reasoning depth via
/effort low→xhigh. Memory persists across CLI/chat/SDK/editor/phone;
self-host option; SDK for embedding. Hosted on US infra.

Safety thesis (video + docs): safety lives **outside** the model -
5 layers starting with command parsing that blocks dangerous commands
even in accept-all mode. Rationale cited: NIST test (DeepSeek agents
12x more likely to follow hijacker instructions), Anthropic backdoor
research (safety training doesn't remove backdoors), Replit/Google
 incidents were command-layer failures not model failures.

## Fit with devin-bundle

- `data/bundle-models.json` + `docs/MODEL-GUIDE.md`: our role→model
  routing is a **static table** edited by hand. Dropstone's monthly
  tier rotation is the same idea productized - lesson: routing tables
  want a review cadence + promotion/demotion semantics, not just values.
- Our PreToolUse hooks (hooks.v1.json chain: dep-audit-gate,
  check-push-green, context-budget, etc.) ARE the external safety
  layer - same architecture, already implemented. Dropstone validates
  the pattern; nothing new to copy mechanically.
- Dropstone itself: hosted service, needs account; self-host exists but
  is infra-heavy. Not a drop-in for our SWE-2-routed bundle.

## Recommendation

**TRACK.** Two portable ideas, both cheap:
1. Add a "lineup review" cadence note to MODEL-GUIDE.md (quarterly:
   re-evaluate role→model picks, record promotions/demotions) - mirrors
   Dropstone's monthly rotation at our scale.
2. Document the external-safety invariant explicitly (already true via
   hooks; worth one line in CONTEXT.md/architecture docs so future
   changes don't move safety into prompts).

No adoption: hosted dependency + our routing already covers the need.

## Evidence

- dropstone.io, docs.dropstone.io/cli/models, support.dropstone.io/
  models/lineup-history (lineups 1.5-1.8 verified)
- Video transcript: .devin/scratch/yt-batch1/transcripts/z5kcsAmoZRo.json
