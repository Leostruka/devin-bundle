# big-file-refactor: 3-phase modularization of oversized files

status: open
priority: P2
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reels 05 + 13 (matheusgomes, same author, same technique, public repo with 3 prompts): files at 5k-15k lines break context, compaction loses it, agent hallucinates. Technique: (1) analyze + code-gates, (2) break by responsibility into modules/classes/functions, (3) verify + wire connections. Transcripts: `transcripts/05-matheusgomes-a.json`, `transcripts/13-matheusgomes-b.json`.

## Recommendation
New skill `skills/big-file-refactor/SKILL.md`: the 3-phase protocol. Phase A inventory (symbols, dependents, cohesion groups); Phase B extraction plan (target module map, one mechanical move at a time, imports rewired per move); Phase C verify (tests green after EVERY move, never a big-bang rewrite). References `lean-code`, `architecture` (seams/strangler), `edge-coverage` (suite must exist first or characterization tests get written). Include the max-lines heuristic (flag >800-1000 lines for splitting per language norms).

## Verification
`ls skills/big-file-refactor/SKILL.md`; manifest + count; audit clean.
