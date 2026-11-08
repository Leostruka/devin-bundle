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

## Sun PM addendum 2 - bug-class sweep exhausted + supply-chain (12:30-14:15)
- AST-driven sweeps across extensions/ AND scripts/ (9 bug classes):
  network timeouts, output overwrites, subprocess timeouts, subprocess
  + file-I/O encoding, exit-code contract, pickle/yaml/eval/shell=True/
  verify=False/mktemp/bare-except, httpx/requests timeouts, archive
  extraction, destructive file ops. All either fixed, verified clean,
  or guarded by new audit checks.
- audit.py checks [36] exit-code contract, [37] subprocess utf-8,
  [38] file-I/O utf-8 - all AST-precise, now scan extensions+scripts
  via shared _scan_py_files(). Summary: ALL 38 CHECKS.
- Fixes this block: last 3 subprocess-without-timeout (harness-tree
  selftest, 2x taskkill), 4 missed text=True decode sites, 8 file-I/O
  decode sites, check-tools renderer timeout (120s + clean FAIL),
  dep-audit x2 utf-8 pins.
- asr/bootstrap.py supply-chain: sha256 pins for whisper.cpp binary
  (GH release digest) + ggml tiny/base/small (HF LFS oid); unpinned
  models refused; cache hash-verified (corrupt auto-refetch, good
  skips download). Live+bundle _cache contents verified MATCH.
- PR bookkeeping: #414 superseded-by-#422 comment (verified
  _validated_schedule covers all cases, both apply paths);
  #421 ancestor-of-#422 comment. All 3 PRs OPEN/MERGEABLE/BLOCKED,
  0 reviews - merge remains user action.
- Suite: 2345 passed / 8 skipped; audit 0/0 at every push.
- Commits: d0aa303, a44098c, 50d1274, 491aa97, 62de03f, 745cf73,
  eab4a14 on fix/gcal-validation-ics (PR #422).
- Learned: never chain `git push` with other commands in one exec -
  the PreToolUse push-gate evaluates pending diff and blocks the
  whole command pre-execution. Commit first, push separately.

## Sun PM addendum 3 - laya G5 calibration evidence (14:30-16:20)
- First real calibration runs for the laya decision backend (issue
  04-laya-jev-rollout, the only "ready" board item). Pipeline was
  built but never executed: authored drafts -> capture_eval (real
  worker, shadow config) -> eval_decisions -> frozen manifests.
- Production profile.json stays mode:off; captures ran against
  .devin/laya/profile.calibration.json (mode:shadow only).
- Results: issue-category-v1 acc 0.684/cov 0.792; output-context-v1
  acc 0.563 (runtime_failure collapse); skill-family-v1 acc 0.421
  cross-domain (0.125 on dev-flavored draft - eval-design flaw
  caught and corrected with v2).
- Cross-profile pattern: accuracy degrades with label cardinality
  (3-way 0.68 / 5-way 0.56 / 7-way 0.42). All below assist
  threshold - no calibration block written, gate stays closed WITH
  evidence. Viable paths documented: <=3-label sets, binary
  reformulations, or different checkpoint.
- Commits: d4cdab5, a4e9324, ce66b1b on fix/gcal-validation-ics.

## Sun PM addendum 4 - laya campaign COMPLETE (14:05-16:05)
- All 14 decision profiles now carry frozen real-worker evidence
  (~250 cases). Continued the <=3-label sweep into every remaining
  profile incl. dynamic-candidate ones (ui-target, skill-pick,
  media-preset built from the real manifest catalog shortlists).
- Contract fixes landed: compact-item-v1 + knowledge-label-v1
  bare-list criteria -> dict-labels (defect class x2); laya-guard
  empty-goal dead lane (every request invalid_request since
  authoring - cmd-risk lane was silently dead).
- Breakthrough: media-intent-v1 is the only viable assist candidate
  (0.966 decided acc; held-out adopted 0.90 @ platt thr 0.9). Fit
  was optimistic vs held-out - documented honestly; shadow-only.
- Meta-laws for future checkpoints: prose/natural-language state
  decides; structured JSON/digest state abstains uniformly;
  distinct intents match, comprehension/trajectory fails.
- Commits: 9928d27, d9091ac, 6b72684, f6a895d, b28ba9d, 8b38bd7.

## Sun PM addendum 5 - held-out batch 2 + UTF-8 root cause (14:52-16:40)
- media-intent-v1 held-out batch 2 (+20 fresh): adopted 13/13.
  Combined held-out 40 cases: 0.9565 adopted acc. Failure mode
  pinned to complaint/observation phrasing.
- fit_calibration.py: platt + PAVA-isotonic map fitting over
  frozen manifests with separate held-out scoring (7 tests).
  Bake-off: table 0.9583 best; no map separates wrong adoptions -
  residual risk is model-side, needs consumer guard.
- Guard trade-off analyzed on frozen data: imperative-only filter
  catches the wrong adoption but also blocks a correct noun-phrase
  request (acc->1.000, cov->0.525). Documented, not shipped.
- ROOT CAUSE: engine_error:TypeError = cp1252 stdio mojibake ->
  lone surrogates -> tokenizer reject. pin_stdio_utf8() fix;
  skill-pick-v1 recaptured 0.882/0.567 (was corrupted 0.133 cov -
  'extreme abstention' was bug artifact); filebool recaptured
  0.500/0.500. Same class swept: mcp_server, cu_session,
  ui_dsl, scrape parse, prompt_compiler, review_gate.
- Issue #431 filed: media-intent activation checklist.
- Commits: 73387f9, d9daf04, 0f0fe21, aa06cb1, e03abc1, 62a19bc.

## Sun PM addendum 6 - audit check [39] closes the stdio class (16:00-16:20)
- New audit check [39] flags text-mode sys.stdin readers without a
  utf-8 pin (reconfigure/pin_stdio_utf8); binary buffer exempt.
- First run caught 4 un-pinned scripts: context-budget,
  context-pressure, file-size-guard, design-lint-gate - the two
  JSON-payload hooks were the real exposure. All pinned with the
  established reconfigure block; live copies + ledger + manifest
  export_hash synced.
- Audit now 39 checks, 0 errors / 0 warnings. Full suite re-run
  before push.

## Sun PM addendum 7 - deadline root cause + activation pre-staging (16:18-16:35)
- deadline_exceeded analysis: 20 misses across frozen manifests,
  16 at case idx 0 = cold-start artifact (~>1s first-request CPU vs
  1000ms budget; steady ~200ms). Residual 4 = heavy-prompt jitter.
- Fix: laya_worker.warm_engine() throwaway predict at startup, wired
  into serve-stdio main + layad serve_socket; live-verified first
  request now returns suggestion. +2 tests. Commit b69c878.
- #431 items 1-4 pre-staged: proposal JSON pins english checkpoint
  (HF rev 7b928d82, artifact sha256 54f69565...) + exact config
  delta; activation_errors dry-run clean. Vendoring note: HF cache
  path fragile, move snapshot before activation. Commit eb8ac74.
- Audit now 39 checks (added [39] stdio decode; caught+fixed 4
  script stdin readers). Suite 2361 green. Commits 6c8af75, b69c878.
