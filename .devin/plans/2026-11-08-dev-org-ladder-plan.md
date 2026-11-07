# Dev-org ladder - tomorrow plan (2026-11-08, Sunday)

Scope: GitHub issue #346 (only open issue) - dev organization tooling,
micro -> macro ladder. Validated state: micro = #345/#348 (agenda-roteiro,
merged), meso = `.devin/scratch` DAGs + wayfinder + planning-pipeline,
macro = `scripts/roadmap-board.py` (#394, merged; live run 190 issues,
94 done). audit.py: 0 errors, 1 warning (pre-existing).

## Blocks (America/Sao_Paulo, UTC-3) - FINAL, written to AGdevin

| Time | Owner | Task | Done when |
|---|---|---|---|
| 09:00-10:30 | agent | File next ISSUE tickets under #346: meso capacity/WIP sprint view, micro ticket timeboxing+WIP, micro focus tracker, macro goal tracker | GitHub issues created, each linking #346 |
| 10:30-11:30 | agent | First real agenda-roteiro run + wire scheduled-turns morning turn + APP.md run log | roteiro emitted from real free/busy; run log updated |
| 14:00-17:00 | agent | Implement meso gap: capacity/WIP view consuming `roadmap-board.py --json` (frontier size vs WIP limits per effort) | script + tests green; board shows capacity column |
| 17:00-18:00 | agent | audit.py + pytest + branch/PR + #346 status comment | checks green; PR open |

## Notes

- DONE 2026-11-07: `[gcal]` credentials configured via oauth_setup.py
  (3 scopes incl. calendar.calendars); Calendar API enabled; first real
  free-busy + plan + apply --confirm wrote the 4 blocks above to the
  AGdevin Google calendar (all confirmed). Roteiro:
  `.devin/scratch/dev-org-ladder/roteiro.json`.
- Calendar reality: all-day "Mensalidade united" on primary is
  informational only (events.list path); timed busy tomorrow = none.
- Dependencies: block 3 consumes tickets from block 1 (can start on the
  meso ticket first); block 4 depends on block 1 output.
- Spillover: micro timeboxing/focus tracker and macro goal tracker stay
  as filed tickets if the day overruns.
- FREE-TIME PROTOCOL (user directive): gaps between/after blocks are
  spent exploring the repo, researching, and architecting+filing issues
  of all types (fixes -> new implementations). Execution brief:
  `.devin/scratch/dev-org-ladder/day-run-2026-11-08.md`.
