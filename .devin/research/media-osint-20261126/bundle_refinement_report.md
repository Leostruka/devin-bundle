# Media OSINT -> devin-bundle refinement report

Date: 2026-11-26  
Input: 8 media URLs in `links.txt`  
Evidence base: `cards/`, `frames/`, `transcripts/`, `metadata_digest.md`, `external/`, `github_repo_snapshot.json`, `verify.md`

## Executive synthesis

The batch converges on one meta-pattern: **expertise must be externalized into durable, testable artifacts before the agent spends tokens building**. The strongest sources do not merely prompt harder; they write a brief/spec, freeze constraints, measure objectively, batch corrections, and use narrow agents for narrow changes.

Two high-value gaps emerged for `devin-bundle`:

1. **Video/motion production workflow**: the bundle has `animation-direction` + `extensions/remotion-render`, but lacks the complete AI Labs-style loop: durable `VIDEO.md`, video-specific slop corpus, browser scrub preview before render, timestamped batched notes, scoped low-cost fixer, measurement-first visual verification, and render only after approval.
2. **Hardware/model inference hill-climbing**: `performance` is generic and `continuous-improvement` has evidence discipline, but the bundle lacks theoretical ceilings, noise-controlled interleaved A/B runs, GPU serialization, memory-cap watchdogs, long-context stability gates, output-equivalence checks, and publication qualification.

A third medium-value gap is **granular UI motion taste**. `frontend-design` + `impeccable` already overlap heavily with Emil Kowalski's skills, but the bundle can selectively absorb motion vocabulary, choreography, gesture/mobile-native checks, strict animation review, and post-session taste learning without importing 18 separate skills.

## Evidence quality summary

| Source | Verdict | Reason |
|---|---|---|
| Prism | Useful adjacent implementation | Repo/features verified; speed claims conditional and mostly self-reported. |
| OpenMAIC | Real project, strong adoption | Repo verified at 44,468 stars; learning efficacy not assessed. |
| Sakuga VFX | Real library, useful design pattern | Repo/site verified; reel itself names no source. |
| squid5090 | Real repo, unverified performance | Benchmarks are author-reported; independent replication not found. |
| inference-optimisation | High-value verified process | Primary SKILL.md contains concrete measurement/gating protocol. |
| Trunk/Isaque 2.0 | Park / do not adopt | Self-published preprint, no citations or independent replication found. |
| Emil Kowalski skills | High-value verified expertise | MIT repo verified at 59,775 stars; direct overlap with bundle design skills. |
| Matt Pocock Parameters | Verified language fact | Standard TypeScript behavior, directly demonstrated. |
| AI Labs motion workflow | High-value pattern, not reproducible verbatim | Screens show detailed contracts, but skills are paywalled; no public repo verified. |

## Prioritized refinement backlog

### P0 - Evolve `animation-direction` into a full video-motion workflow

**Evidence:** `cards/eFog2ttK95g.md`; frames `eFog2ttK95g_04.jpg` through `_13.jpg`; transcript lines 344-460, 531-598.  
**Current bundle state:** `animation-direction` already covers narration -> scene-plan v2 -> approval -> Remotion render -> ffmpeg composite, with `plan_check.py`.  
**Gap:** no durable video brief schema, no video-specific slop corpus, no browser scrub/review loop, no timestamped note protocol, no scoped fixer contract, no measurement-based visual verifier.

Recommended refinement:

1. Add a `VIDEO.md` contract as the single source of truth: goal, audience, aspect/duration, copy, timed shot list, palette/type, motion, sound, assets, constraints, approval state, build notes.
2. Add video-specific `slop-video-patterns` reference: centered title on gradient, fake timecodes/corner labels, card/frame borders, dead-center static shots, slide-deck resets, meaningless motion.
3. Extend `extensions/remotion-render` or add a sibling preview tool that serves the unrendered composition in a browser with play/scrub and exact timestamp comments.
4. Batch notes by scene; classify small text/color/size/timing edits separately from design changes.
5. Add a `video-fixer` agent profile with hard scope: only copy, font sizes, dimensions, colors, timings; never redesign, add scenes, alter layout, refactor, install packages, or create/delete files.
6. Verify by measurement first: DOM geometry, exact beat/cut times, font/color values, viewport/responsiveness, generated asset dimensions; use cropped screenshots only when measurements cannot answer the question.
7. Render MP4 only after explicit approval.

Why first: directly reduces token burn, context churn, and rebuild loops, which are core bundle constraints.

### P1 - Add an `inference-optimisation` skill or absorb its protocol into `performance`

**Evidence:** `cards/DgLtA_qSr5D.md`; `external/inference_skill.md`; `external/inference_levers.md`.  
**Current bundle state:** `performance` covers baseline/profile/fix/re-measure generically; `continuous-improvement` covers evidence/held-out discipline.  
**Gap:** no model-serving-specific optimization loop.

Portable protocol worth importing:

- compute theoretical ceilings before touching flags: decode memory-bandwidth bound, prefill compute bound, TTFT/startup/KV floor;
- inventory hardware, memory type/size, driver, engine, model, quantization, launch command;
- one change per experiment;
- at least 6 decode samples, median, control-candidate-control interleaving;
- fixed environment, serialized GPU jobs, memory watchdog, no forced mid-batch kill;
- stability gates: long-context needle retrieval, concurrent soak, greedy output equivalence for allegedly lossless changes;
- `PLAN.md` + `ledger.jsonl` including failures;
- plateau declaration after three consecutive in-noise levers;
- clean pinned build qualification before publication.

Implementation choice: a compact new skill is cleaner than bloating `performance`; it can reuse the MIT-licensed source with attribution or be rewritten from the observed method.

### P1 - Selectively strengthen UI motion/design taste

**Evidence:** `cards/5cQUE-9Gtyw.md`, `cards/DgHqphRRXo4.md`; `external/emil_*`; `external/sakuga_README.md`.  
**Current bundle state:** `frontend-design` sets distinctive direction; `impeccable` audits/polishes with lint, state coverage, anti-slop patterns, and bounded critique loops. This is already strong.  
**Gap:** granular motion expertise is dispersed and less operational than Emil's skill family.

Recommended compact additions, preferably one `ui-motion` skill/reference rather than 18 new skills:

- animation vocabulary: exact terms for stagger, spring, shared layout, pop/bounce, anti-patterns;
- choreography: lead/support/detail roles, parallel-vs-sequence decisions, 30-80ms product staggers, keep groups under roughly 300ms when appropriate;
- animation performance: transform/opacity first, avoid layout thrash, reduced-motion fallback;
- gestures/mobile-native: 1:1 finger tracking, release velocity, mid-animation interruption, sticky hover/tap-highlight/100vh/input-zoom/safe-area checks;
- break-ui: worst-case data pass with long names, huge counts, empty states, one-letter names;
- learn-taste: after corrections, distill user edits into project `DESIGN.md` rules with reasons;
- Sakuga principle: explicit rest -> anticipation -> hit -> follow-through -> settle keyframes; effects must amplify meaning, not decorate by default.

### P2 - Add utility-type extraction examples to `typescript-node`

**Evidence:** `cards/RSG2qySs0ps.md`.  
Small insertion: when a library does not export parameter types, use `Parameters<typeof fn>[n]`, plus related `ReturnType<typeof fn>` and `Awaited<ReturnType<typeof fn>>` patterns. Include a caution about tuple positional brittleness when library signatures change.

### P2 - Steal resilient-download ideas, not the Prism product

**Evidence:** `cards/DgCwVKpvkYm.md`; `external/prism_README.md`.  
Potential applications inside existing bundle surfaces:

- media acquisition: resume partial downloads and verify file/version changes;
- model acquisition: checksum verification and selective file download;
- video workflows: frame-accurate clipping as a first-class ffmpeg operation.

Do not build or embed a download manager; document/evaluate Prism as an optional external tool only if a recurring need appears.

### P3 - Treat OpenMAIC as adjacent-pattern recon only

**Evidence:** `cards/DgGh9C1AHTp.md`; `external/openmaic_README.md`.  
Interesting patterns: role-based teacher/classmate agents, durable course artifact, interactive scenes, offline export. No direct bundle gap unless the user wants education/course generation. Keep as reference for future agent-artifact design.

### Rejected / parked - Trunk and Branches

**Evidence:** `cards/DfuvBDqRQ8R.md`; `external/trunk_README.md`.  
Do not import architectural claims. The project is self-published, low-adoption, and extraordinary claims lack independent replication. It still reinforces a useful bundle rule: raw receipts and frozen baselines are necessary but not sufficient; extraordinary performance/retention claims require held-out reproduction.

## Suggested next actions

1. Turn P0 into a planning ticket/spec for `video-motion-workflow` or an `animation-direction` v2.
2. Turn the inference protocol into a draft skill in a separate implementation session, with held-out validation criteria before adoption.
3. Run a drift/gap pass over `frontend-design` + `impeccable` and add only missing UI-motion rules, keeping context lean.
4. Make the TypeScript utility-type insertion as a micro-edit when approved.

## Reproducibility notes

- Download/metadata extraction: `source_map.json` shows 8/8 sources with media and metadata.
- Contact sheets: 37 sheets generated across all 8 sources.
- ASR: 8/8 transcripts returned `ok:true`; `DgHqphRRXo4` was music-only.
- YouTube caption downloads mostly hit HTTP 429; only `RSG2qySs0ps.en.vtt` was retrieved. ASR is the transcript source for the other videos.
- Large video files were kept in `C:\Users\leand\AppData\Local\Temp\media-osint-20261126-cache\media` because the D: drive reached 100% capacity; small metadata, frames, transcripts, cards, and reports are in this directory.
