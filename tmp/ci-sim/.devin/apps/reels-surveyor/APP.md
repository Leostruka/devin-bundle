# Reels Surveyor (reels-surveyor)

intent: survey saved Instagram reels and convert them into systematic bundle issues
kind: agentic-app
schedule: on-demand (user supplies a reel list or says "check the saved collection")
inputs: reel URLs or the Arc saved-collection (via computer-use), extensions/asr local pipeline
outputs: transcripts in .devin/scratch/reels-N/transcripts/, survey in .devin/research/, issues in .devin/scratch/reels-N/issues/, plan in .devin/plans/
done-when: every reel has a verdict (ADOPT/ADAPT/COVERED/BACKLOG/skip), every adopted item has a canonical issue file, plan written, changes merged to main

## Prompt

For each reel URL: transcribe with `python extensions/asr/transcribe.py <url> --lang pt` into `.devin/scratch/reels-N/transcripts/<id>.txt`. If the user points at the saved collection instead, enumerate it via computer-use carousel + URL bar reads.
Decode each transcript against the current bundle (manifest.json, skills/, .devin/docs/): mark ADOPT (new skill/hook/agent), ADAPT (edit existing), COVERED (already shipped), BACKLOG (external dependency) or skip. Write the survey table to `.devin/research/<date>-reels-batchN-survey.md`, one canonical issue per actionable item in `.devin/scratch/reels-N/issues/` (status/priority/source/Evidence/Task), and a wave plan in `.devin/plans/`. Then execute the waves: implement, update manifest hashes, audit, test, changelog, PR. Close each issue with an Answer section.

## Run log

- 2026-11-05 batch-2: 16 reels -> 15 issues -> all resolved (#310-#322)
- 2026-11-05 batch-3: 10 slots -> 9 transcribed -> 3 issues resolved (#331)
- 2026-11-06 batch-4: 5 reels + SWE-2-Flash -> 8 issues -> resolved (#339); follow-up evals OpenViking/Artemis (#340)
- 2026-11-12 batch-8: 11 reels + 2 web links + busybar re-check -> 7 issues (#567-#573) -> 5 resolved (PRs #574-#576: ext UTF-8 pins x36, data-analyst glossary, perf load-test playbook, tool pointers), #570 spike validated (.devin/research/2026-11-12-rune-spike.md), #572 backlog (GPU eval next sprint); infra find: transcribe.py stdout cp1252 fixed
