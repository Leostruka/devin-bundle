# Week roteiro - 2026-11-09 to 2026-11-13 (America/Sao_Paulo)

Built 2026-11-07 from: 19 verified issues filed in self-improvement loop
(#395-#413) + carried-over #346 work. Real free/busy: ZERO timed busy
events Mon-Fri (all_day informational only: "Mensalidade united" 11-08,
"Aniversário da yas" 11-11). Slots = work windows 09-12 + 14-18 BRT.

Roteiro: `.devin/scratch/dev-org-ladder/roteiro-week.json`
(10 tasks, 0 unscheduled, 780min slack, overcommit=false)

| Day | Blocks |
|---|---|
| Mon 09 | 09:00-11:30 gcal crash/validation (#395,#409,#413); 14:00-16:30 ics correctness (#396,#397,#398); 16:30-18:00 oauth #411 |
| Tue 10 | 09:00-12:00 write-path (#399,#400,#401,#410); 14:00-17:00 status vocab (#402,#403,#405,#407) |
| Wed 11 | 09:00-10:30 scratch hygiene #406; 10:30-12:00 PS preflight #412; 14:00-16:00 infra hooks (#404,#408); 16:00-18:00 closeout PRs/audit/#346 |
| Thu 12 | ~~09:00-11:30 meso capacity/WIP view~~ DONE Sun → **09:00-11:30 yt-batch1** (6 YT links → transcripts → survey → issues); **14:00-16:00 evals #415/#416**; **16:00-18:00 overflow + ladder scoping #418/#419/#420** |
| Fri 13 | overflow/buffer + spillover from earlier blocks + #418-#420 implementation pick |

Notes:
- Greedy first-fit front-loads the week; Fri stays free as buffer.
- "Week closeout" landed Wed 16:00-18:00 (first fitting slot) - if PRs
  aren't ready by then, defer to Fri.
- Free-time protocol (day-run-2026-11-08.md) applies to ALL gaps:
  explore -> research -> architect -> file issues. No idle time.
- Sunday 11-08 blocks already on AGdevin calendar (4 events confirmed).
- Week events WRITTEN to AGdevin 2026-11-07 ~21:05 (10 created, 0
  failed, prefix "[week] ").

## Revised 2026-11-08 PM (post-Sunday execution)

- **#417 capacity/WIP view DONE early (Sun)**: `roadmap-board.py` gained
  `capacity()` - per-group open/ready/blocked/in_flight + `--wip-limit`
  + `## Capacity` markdown section + JSON `capacity` block. Live:
  190 issues, frontier 95, blocked 1, in_flight 0.
- **New GitHub issues filed Sun AM** (children of #346): #417 (done),
  #418 micro timeboxing, #419 micro focus tracker, #420 macro goal
  tracker. Plus reels-6 evals #415/#416.
- **Capacity insight**: `edge-audit` effort alone holds 61 open/ready
  issues (of 190 total) - largest frontier concentration; triage
  candidate, not this week's scope.
- **Thursday re-planned on AGdevin**: capacity event patched → yt-batch1;
  2 events added (evals #415/#416, overflow+ladder scoping).
- **scheduled-turns wired**: `.devin/scheduled/agenda-roteiro.md` prompt
  ready; user registers `devin-agenda-roteiro` task (09:00 daily) - agent
  never self-registers per skill guards. Monday roteiro already run:
  `.devin/scratch/dev-org-ladder/roteiro-2026-11-09.json`.
- **yt-batch1 status**: 5/6 video metadata in `.devin/scratch/yt-batch1/
  meta.txt` (missing g_NgCLTibiM); transcripts+survey pending → Thursday.
- Ladder children #418/#419/#420 are NEXT-week candidates (Fri buffer or
  following week); #417 proved the pattern.
