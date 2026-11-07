# docs: SLEEP framework pointer (Google continual-learning paper)

status: ready-for-agent
priority: P3
source: reels batch-5 survey, parthknowsai DfZuDIUOGJZ; eval already done in batch-4 follow-up

## Evidence

Transcript (`.devin/scratch/reels-5/transcripts/DfZuDIUOGJZ.txt`): "Google just taught an AI to rewrite its own weight... by sleeping": wake/sleep lifecycle, sleep phase consolidates short-term knowledge into long-term parameters, mitigates catastrophic forgetting.

Verified: Google Research blog 2026-10-27 + paper "Language Models Need Sleep: Learning to Self-Modify and Consolidate Memories" arXiv:2606.03979 (Behrouz, Hashemi, Javanmard, Mirrokni). Sleep phase = memory consolidation via distillation into weights + low-rank MoE expert growth + "dreaming" RL replay. Research-only: no code/weights; metrics not independently reproduced. Name collision: arXiv:2605.26099 is a DIFFERENT same-titled paper; cite 2606.03979 only.

Already evaluated: `.devin/research/2026-11-06-reels-batch4-survey.md` follow-up table ("SLEEP framework = periodic memory consolidation; analogs already in bundle: memory hooks + self-improvement; dreaming ~ create/maintain-verification-skill").

## Task

Doc-only cross-link: wherever the batch-4 follow-up SLEEP row lives, add the reel citation (parthknowsai DfZuDIUOGJZ, this survey) so future readers connect coverage -> eval. If a memory/self-improvement doc (`skills/memory-management`, `skills/continuous-improvement`, or `.devin/research/INDEX.md`) lists external analogs, add one line pointing to the SLEEP eval with the arXiv ID. No new analysis; the eval exists.

## Acceptance

- [ ] Reel->eval cross-reference recorded in the appropriate existing doc
- [ ] arXiv:2606.03979 cited (not the 2605.26099 collision)
