# coverage matrix for guilhermemorais 10-repo roundup

status: resolved
priority: P3
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 03 lists 10 repos: task-master, serena, codebase-understanding tools, superpowers, trail-of-bits artifacts, STRIX pentest agent. Transcript: `transcripts/03-guilhermemorais.json`.

## Recommendation
Confirm the mapping in the survey: task-master ~= afk-loop DAG; serena ~= researcher/subagent_explore; STRIX ~= red-team-lead + offsec-tools + rea-ops; superpowers ~= skills corpus; understanding ~= research/domain docs. Anything not mapped gets a one-line backlog entry. Output: extend the survey table's verdict column to mark each covered/skipped.

## Verification
Survey file lists all 10 with bundle counterpart or explicit skip.

## Answer

Matrix in `.devin/research/2026-11-05-r2-evals.md`: 7/10 items covered by existing machinery (afk-loop, researcher, security-audit-cf, red-team-lead, frontend-design); 4 unverifiable names skipped - no blind adoption.
