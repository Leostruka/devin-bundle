# jtrivard power features: watchdog agent + ultrathink + compact-early

status: open
priority: P2
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 11 (j.t.rivard): (a) agent watching the agent, flagging missed items; (b) /loop fixed-interval tasks; (c) compacting before context pollution (~half window); (d) JS-coordinated agent swarm; (e) ultrathink = max reasoning for one turn. Transcript: `transcripts/11-jtrivard.json`.

## Recommendation
Three deliverables: (1) `agents/watchdog.md` profile or `skills/watchdog` - runs parallel to a work session, diffs claimed output vs actual state, reports misses (extends chief-of-staff's env-watch idea to work-quality). (2) compact-early guidance added to `context-hygiene` SKILL.md (threshold recommendation + why end-of-window degrades). (3) `max-effort` note in `docs/MODEL-GUIDE.md`: how to escalate reasoning effort for one turn when the CLI supports it. /loop and swarm coordination are covered by `afk-loop` and orchestration skills - note as covered.

## Verification
Watchdog artifact exists; both doc edits land; audit clean.
