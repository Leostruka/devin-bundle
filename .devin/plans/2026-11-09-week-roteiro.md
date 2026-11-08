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
| Thu 12 | ~~09:00-11:30 meso capacity/WIP view~~ DONE Sun -> **09:00-11:30 yt-batch1** (6 YT links -> transcripts -> survey -> issues); **14:00-16:00 evals #415/#416**; **16:00-18:00 overflow + ladder scoping #418/#419/#420** |
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
- **Thursday re-planned on AGdevin**: capacity event patched -> yt-batch1;
  2 events added (evals #415/#416, overflow+ladder scoping).
- **scheduled-turns wired**: `.devin/scheduled/agenda-roteiro.md` prompt
  ready; user registers `devin-agenda-roteiro` task (09:00 daily) - agent
  never self-registers per skill guards. Monday roteiro already run:
  `.devin/scratch/dev-org-ladder/roteiro-2026-11-09.json`.
- **yt-batch1 status**: 5/6 video metadata in `.devin/scratch/yt-batch1/
  meta.txt` (missing g_NgCLTibiM); transcripts+survey pending -> Thursday.
- Ladder children #418/#419/#420 are NEXT-week candidates (Fri buffer or
  following week); #417 proved the pattern.

## Revised 2026-11-09 AM (Sunday execution, ahead of schedule)

Everything below landed Sunday on `fix/gcal-validation-ics` -> PR #422
(+ #421 for capacity). Week blocks Mon-Wed are effectively DONE:

- **gcal**: #395-#401, #409-#411, #413 (267884c, 4104308) - validation,
  ICS TZID/all-day/RRULE, OAuth state+PKCE, idempotent writes, CalDAV
  parity, --flag=value normalization.
- **status vocab / roadmap**: #402,#403,#405,#407 (cb550fb) +
  #406 archive sweep (547400e) - board now 97 live issues, frontier 5.
- **infra**: #404 dep-audit budget (7165cb4), #408 metrics rotation
  (b1e57c6), #412 PS5.1 preflight (3e1c0d7).
- **ladder children**: #418 estimate/actual fields (e173777), #419
  focus.py tracker (0099185 + --root fix), #420 .devin/goals rollup
  (19f81c5) - micro/meso/macro ladder complete end-to-end.
- **evals**: #415 Rune note, #416 MiroFish note (e09139e).
- **yt-batch1 DONE early**: 6 transcripts, survey
  `.devin/research/2026-11-09-yt-batch1-survey.md`, 4 eval issues
  #423-#426. Evals executed same day: agent-desktop ADOPT-EVAL (live
  UIA verified -> spike #427 -> module landed 2cde8aa -> contract follow-up
  #429), stageshow TRACK+pattern (#428 done), dropstone TRACK (cadence
  note in MODEL-GUIDE.md), pr-agent TRACK (no provider key).
- **Verification**: pytest 2273+8skip, audit 0/0 at each push; push-gate
  caught + fixed a real em-dash violation (stop-guard).

**Remaining for the week** (frontier, not scheduled):
- ~~#429 agent-desktop Backend contract~~ DONE Mon AM: DesktopBackend
  (option A tree-native) + open_backend kinds desktop/agent-desktop,
  live-verified, 16 tests (4cc80bd). Issue closed.
- ~~#423-#426 evals~~ DECIDED + closed: #423 adopted (via #427/#429),
  #424/#425/#426 track-as-pattern. #428 landed + closed.
- ~~#430 ASR PT-BR~~ DONE + closed: model resolution + lang detection +
  warnings; verified live (--model small --lang pt = clean PT-BR).
- Review-hardening batch on PR #422 (3cb348c): all 9 reviewer findings
  fixed + 8 regression tests; PR comment posted.
- Local frontier: 5 ready issues (ISSUE_02-05 media/AI epics,
  MILESTONE_2_12 agent_rts) + 1 egm-laya open - sprint-scale, pick per
  capacity view
- Fri 13 stays buffer/overflow as planned

## Revised 2026-11-09 midday (Sunday continuation)

- **GitHub tracker cleaned**: 26 completed issues closed with evidence
  comments (#395-#413, #415-#420, #427) - only umbrella #346 remains
  open. `.devin/research/INDEX.md` drift fixed (eval notes + epic
  origins + office wave now indexed).
- **ISSUE_04 COMPLETE e2e**: composite.py (ffmpeg overlay step 6) +
  narrated-clip proof - SAPI narration -> transcribe -> plan ->
  plan_check -> Remotion 822f -> composite -> final-narrated.mp4.
  Two real bugs found+fixed en route: mp4 silent-empty in transcribe
  (whisper demuxes wav/mp3 only), plan_check prop-contract gap
  (counter `to` vs `value` crashed render mid-flight).
- **ISSUE_02 partial**: eval_set.py held-out harness + FIRST real-data
  eval - real 3/3, synth JPEG false-positives at default thresholds
  (JPEG quant signature dominates ref residual). Documented; needs
  bigger dataset for calibration.
- **ISSUE_05 partial**: photo_qc live-verified on real webcam set -
  go/correct verdicts correct on consistent vs mixed captures.
- **egm BitNet measured**: i2_s = 35.4 tok/s but degenerate quality
  (3/3 repetition loops) - NOT viable as decision backend; options
  recorded in issue.
- Commits this block: 1ebd2ab, aa30f1b, 61c8046, 2cdc837, 2ff8fc0,
  360d3d5 on fix/gcal-validation-ics (PR #422).

## Sun PM addendum - extension audit sweep (12:00-12:30)
- Full first-party surface scan: 28 extensions + 45 scripts. 6 real
  fixes shipped (overwrite guards x4, https+size-cap, missing
  exists-check, unbounded subprocess) - commits fc89926..6096e0c.
- Verified-clean list in self-improvement ledger iter 9.
- Suite: 2337 passed / 8 skipped; audit 0/0 at every push.
- Frontier unchanged: held-out datasets (ISSUE_02/05), craft CLIs
  (ISSUE_03), PR merges + scheduled-task registration (user actions).
