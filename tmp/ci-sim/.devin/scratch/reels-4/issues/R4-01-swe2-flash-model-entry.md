# swe-2-flash: add model entry + routing note

status: resolved
priority: P2
source: reels batch-4 survey (.devin/research/2026-11-06-reels-batch4-survey.md)

## Evidence
Cognition launched SWE-2 Flash 2026-11-04: post-train of Inkling-Small (276B total / 12B active MoE, Apache-2.0 base - first non-Chinese base). Devin Desktop + CLI only, free through 2026-11-30, ~200 tok/s vs SWE-2's 60, one-fifth the price. No API, no public weights (secure sharing program for partners). Benchmarks self-reported.

## Task
Add swe-2-flash to data/bundle-models.json models[] with free_until note; add MODEL-GUIDE row recommending it for medium/low-effort routing + cheap subagents during the free window; keep caveats (self-reported evals, no endpoint).

## Answer

Added swe-2-flash entry (role fast, effort medium, free_until note) to data/bundle-models.json + Fast lane row and launch note in docs/MODEL-GUIDE.md.
