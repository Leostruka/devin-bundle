# Ledger: cyclic bundle review (deadline 23:10 local)

DELEGATION: disabled (no subagent authorization this session)
SCOPE: AGENTS.md, skills/, scripts/, config.json, docs/, tests/ (add-only)
INPUT_REGISTER:
- I1 user goal: active cyclic review, GitHub best practices, until 23:10
- I2 issue #699: anti-distraction rules gap (code-over-docs, plan-overlap)
- I3 issue #698: caldoai untangle/prune eval
- I4 issue #700: knowledge stores eval
- I5 issue #431: laya media-intent
SOURCE_REGISTER:
- S1 survey .devin/research/2026-11-18-yt-batch5-reels11-survey.md (verified, this repo)

## Cycle 1: #699 anti-distraction rules (CHANGE_CLASS: config)

OUTCOME: agents treat stale docs/plans as tasks (side quests)
CHECK: grep AGENTS.md for precedence/plan-overlap rule -> absent
EXPECT: no existing rule covers doc-vs-code precedence
EVIDENCE: rule index 1-30 has no source-of-truth precedence entry;
  Rule 7 covers scope-limit but not doc trust hierarchy. #699.

Plan: add terse non-pinned rule 6 (free slot): code-over-docs
precedence + report mismatch; plan-overlap check before building
unticketed work from plans/notes. Keep to ~4 lines (Rule 18 lean).
