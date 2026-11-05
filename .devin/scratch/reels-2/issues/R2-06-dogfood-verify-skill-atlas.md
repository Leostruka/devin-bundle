# dogfood create-verification-skill on the Pages atlas

status: open
priority: P3
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 06 (techbro video 1/7) describes exactly the pattern adopted in #309. The atlas is a live app with a real surface (REPL, tabs, modal, palette).

## Recommendation
Run `create-verification-skill` against https://leostruka.github.io/devin-bundle/ (or local dist) to generate `skills/verify-atlas/` with a feature map (boot, tabs, repl commands, modal, palette). Proves our vendored skill end-to-end and gives the repo its first verify-* skill as a worked example. Note: site is static, so the drive harness is headless-browser screenshot+DOM checks.

## Verification
`skills/verify-atlas/` exists with SKILL.md + features/; one feature proven end-to-end.
