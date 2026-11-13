# Reels batch-7 + YT batch-2 issue map

Survey: `.devin/research/2026-11-10-reels-batch7-survey.md`
Milestone: GitHub #14 (reels-7 deep-eval 2026-11-10, deadline 17:00).
Issues tracked on GitHub (per 2026-11-07 directive).

Inputs: 28 unique links (24 reels + 4 YT). Transcripts:
`.devin/scratch/reels-7/transcripts/`, `yt-batch2/transcripts/`.

| Issue key | GH | Title | Pri | Source(s) |
|---|---|---|---|---|
| R7-01 | #434 | pulse-executor: drain rts intents into afk-loop step | P2 | YT GRlcm3wmOqs |
| R7-02 | #435 | subagent trace+budget contract | P2 | YT GRlcm3wmOqs |
| R7-03 | #436 | decision queue (.devin/decisions.jsonl) | P3 | YT GRlcm3wmOqs |
| R7-04 | #437 | done-evaluator: small-model grades turn-done | P2 | DfieBCtlK5q |
| R7-05 | #438 | done-when contract in dispatch briefs | P2 | Dff39V1vpj7 |
| R7-06 | #439 | rules->control coverage audit | P2 | DeWwjvyiV2_ |
| R7-07 | #440 | activation-guided weight patching PoC | P3 | DfcaHjbEYtq |
| R7-08 | #441 | Dory1.0-4B loop sweep on laya heldout | P3 | YT vSCYL8ySh9g |
| R7-09 | #442 | graphify query -> memory-retrieval | P3 | DcEBQNPNPzs |
| R7-10 | #443 | raea vs Remotion backend spike | P3 | DfgQMGEKGJG |
| R7-11 | #444 | Jev API cloud tier over laya | P4 | DfWJElGNZDz |
| R7-12 | #445 | design state/motion coverage rules | P3 | DcjkR2PSkml DeK0AFcIRhf DfbKtE6iabf DfYRPKEDSDJ DfUdibshw3A |
| R7-13 | #446 | bounded design-iteration converge-by-gate | P3 | YT DByAR5Su1Yw |
| R7-14 | #447 | periodic simplify/cleanup pass | P4 | DfdYAW1xcHk |
| R7-15 | #448 | LGPD questionnaire scope decision | P4 | DfXFwwCDFMD |
| R7-16 | #449 | skills-debt audit step + persona->process | P4 | DffnUDcDBCL |
| R7-17 | #450 | busybar focus status push spec | P4 | DfXwuL0izsO |
| R7-18 | #451 | device-automation lane doc | P4 | YT KDyPHt4lW60 |

NOTE-only: Project Nomad (DfgwiprT5DN), login-bots interview (DejYAGbxOAM),
audit-moat discourse (DcCoPrCxPT_), backprop explainer (De12iBYTUNB),
seasonal-forecast explainer (DfXRHe9s8kZ), music reel (DfHOBy6gCye),
cyberspace edit showcase (DdXZrIMIYXM), JEPA PRH eval (DffOrNAByFw - deferred).

## Outcome status (2026-11-10, in-flight)

| GH | Status | Deliverable |
|---|---|---|
| #434 | CLOSED | scripts/pulse.py - RTS intents drained to afk-loop frontier |
| #435 | CLOSED | scripts/subagent-trace.py + dispatch contract |
| #436 | CLOSED | scripts/decision-queue.py + roadmap-board pending_decisions |
| #437 | CLOSED | scripts/done-evaluator.py + afk-loop writer-is-not-grader gate |
| #438 | CLOSED | task-brief.py --require-done-when (exit 4) |
| #439 | CLOSED | scripts/rules-coverage.py - 74.3% rule->control coverage |
| #440 | CLOSED | extensions/ai-tools/weight_patch.py PoC - defect induction works, iterative repair converges slowly, control regresses |
| #441 | RUNNING | Dory1.0-4B k={1,2,4} sweep on laya heldout - fork-built llama.cpp (PR #30306), CPU |
| #442 | CLOSED | scripts/graph-query.py - 5/5 top-2 vs grep 11-248 unranked |
| #443 | CLOSED | .devin/evals/raea-vs-remotion - verified, hybrid recommendation |
| #444 | CLOSED | .devin/evals/jev-cloud-tier - verified, spike deferred |
| #445 | CLOSED | impeccable SKILL state x motion coverage |
| #446 | CLOSED | impeccable SKILL converge-by-gate bounded iteration |
| #447 | CLOSED | scripts/simplify-scan.py rot scan |
| #448 | CLOSED | skills/lgpd-questionnaire skeleton (skill 182) |
| #449 | CLOSED | audit check [40] skills-debt + persona->process note |
| #450 | CLOSED | extensions/busybar/push.py skeleton + eval doc |
| #451 | CLOSED | .devin/docs/DEVICE-AUTOMATION-LANE.md |

Result: 17/18 closed with shipped deliverables or documented decisions.
