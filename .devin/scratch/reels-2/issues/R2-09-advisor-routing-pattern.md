# advisor pattern: cheap main + escalation consult for hard calls

status: resolved
priority: P2
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 09 (rodrigotadewald): routing command sets main model cheap (Sonnet-class), subagents cheapest (Haiku-class), and hard decisions (architecture, weird bugs) escalate to the strongest model (Opus-class). Transcript: `transcripts/09-rodrigotadewald.json`. Bundle has `data/bundle-models.json` + Rule 20 effort routing but no explicit consult-escalation pattern.

## Recommendation
Extend the routing doc (`docs/MODEL-GUIDE.md`) and/or `data/bundle-models.json` with an `advisor` role: default work on medium/max, and a documented pattern where a subagent or second opinion on the strongest available free model is consulted for architecture/bug-dead-end decisions. Check what Devin CLI exposes for mid-run model escalation (devin-config skill); if nothing exists, document the manual pattern (spawn `architect`/`reviewer` profile for the consult).

## Verification
Doc/role update lands; devin-config confirmed what CLI supports.

## Answer

`advisor_role_model: swe-2-max` added to `data/bundle-models.json`; MODEL-GUIDE gained the 'Escalonamento pontual + advisor' section (Alt+T one-turn max + architect/reviewer subagent as the consult mechanism).
