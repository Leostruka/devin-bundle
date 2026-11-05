# evaluate multi-agent job-application pipeline (alvim reel)

status: open
priority: P3
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 02 (alvim_ai): repo pipeline where agent 1 writes code + cover letter from a job link, agent 2 researches the company and critiques the resume, agent 1 warns before submission. Transcript: `transcripts/02-alvim.json`.

## Recommendation
Backlog-eval: locate the repo (AI JobSert or similar), check license, map the 3-agent chain onto `run_subagent` + `researcher`/`copywriter` profiles. Deliverable is an eval table (ADOPT/ADAPT/SKIP) in `.devin/research/`, not the feature itself. Niche but a clean multi-agent handoff pattern that also demos `arena`.

## Verification
`.devin/research/` file exists with repo link, license, and verdict.
