# dogfood create-verification-skill on the Pages atlas

status: resolved
priority: P3
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 06 (techbro video 1/7) describes exactly the pattern adopted in #309. The atlas is a live app with a real surface (REPL, tabs, modal, palette).

## Recommendation
Run `create-verification-skill` against https://leostruka.github.io/devin-bundle/ (or local dist) to generate `skills/verify-atlas/` with a feature map (boot, tabs, repl commands, modal, palette). Proves our vendored skill end-to-end and gives the repo its first verify-* skill as a worked example. Note: site is static, so the drive harness is headless-browser screenshot+DOM checks.

## Verification
`skills/verify-atlas/` exists with SKILL.md + features/; one feature proven end-to-end.

## Answer

`.devin/skills/verify-atlas/` created per create-verification-skill protocol (project-local, correct home for app-specific verify skills). Feature map: boot/tabs/repl/modal/palette. Proven end-to-end: build+serve+doctor+DOM checks+screenshot in `.devin/scratch/verify-atlas/run1/` (boot renders real stats: 178 skills).
