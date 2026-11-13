# Project State - 2026-11-10 (improvement-loop snapshot)

## Position

Main `51e8ab0` (origin synced). CLI `3000.12.43` installed = latest;
bundle validated against it (`validated_cli_version` bumped in #457).

## Merged today (post-reels-7)

| PR | What |
|---|---|
| #469 | fail-soft annotation wave: 103 `except: pass` sites annotated -> except_pass 0 |
| #470 | silent-error-review scans `tool_response.overflow_path` (field verified on 12.43); <=8 MB, fail-soft |
| #471 | simplify-scan: module-level defs only + pytest-fixture skip (unreferenced_def 30->13) |
| #472 | install-ledger: `.devin/` path remap for live docs/plans/templates (false drift 75->0) |
| #473 | dead-code removal + def-line `# public-api` annotation convention; install-ledger rendered-file currency (source_hash compare) + build-artifact exclusion (.pyd/.so/.dll) |
| #476 | push-gate green cache (HEAD+tree fingerprint, `.git/push-green.json`) + corpus-index noise exclusion (24k venv entries -> 1411 real) |
| #458 | laya worker: `raw_runner_up_probability` (distribution OR probabilities keys) |
| #459 | simplify-scan precision: comments-only markers, annotated-pass, pytest-def skip (2612->149 items) |
| #460 | handoff skill: acp-summarizer 3-section schema (Overview/Breadcrumbs/Current State) |
| #461 | pulse: bold-colon Status/Blocked-by + status_vocab canonical statuses + archived-effort exclusion (168->75 phantom removal; real claimable = 0) |
| #462 | DRS blueprint spec draft (live verify platform-blocked) |
| #463 | laya margin evidence: runner-up recapture, margin gate rejected (#431 item 5) |
| #464 | CLI 12.43 compat doc: ACP modes + client fs-gateway verified |
| #479 | **api-bridge v0.1** (#478): OpenAI-compatible local API over `devin -p` — `/v1/chat/completions`+`/v1/models`, LAN-token gate, E2E "bridge"->"ponte" |
| #480 | api-bridge v0.2: model validation, error taxonomy (400/502/504), estimated usage |
| #481 | api-bridge v0.3: `--concurrency` backend semaphore, CORS preflight, `x-ignored-params` honesty field, self-describing `GET /`, `devin`-alias bug fix (live-verified) |

All PRs merged except #481 (auto-merge armed, CI running). New debt
tracker: **#474** (7 oversized files + push-gate 150s wall time —
`pytest -n 4` measured: no speedup, long-tail bound). Open issues:
#431 (deliberate Laya gate), #474, #478 (bridge tracking — ACP
backend + true streaming deferred there).

## Verified findings worth remembering

- **pulse frontier was blind**: `**Status:** resolved` (17 files) never parsed -
  bold wrapping the colon defeated the regex; plus non-canonical statuses
  ("implemented locally.") fell through. Now consumes `status_vocab.py`.
- **Local Markdown issue DAG is empty**: all 168 scratch issues resolved.
  Frontier `next: None` is correct. Remaining work lives on GitHub (#431) and
  macro epics (ISSUE_02/03/05 in-progress, MILESTONE_2_12 blocked on #216).
- **ACP protocol**: session modes (accept-edits/smart/ask/plan/bypass) are
  settable; in ask/plan the agent delegates fs access to the CLIENT via
  `fs/read_text_file` requests - client-gated read-only oracle; undeclared
  capability = silent deadlock. Working client: `.devin/scratch/acp-spike/client.py`.
- **laya media-intent activation exhausted at map-level**: platt saturates,
  margin gate inside correct band (mi-h14 0.9365), isotonic calibrates the
  error to 1.000. Failure is model ranking, not score shape. Next levers:
  per-class reliability or different checkpoint. #431 stays open deliberately.
- **DRS**: org not entitled (`blueprint-list` -> Organization not found);
  spec drafted for when access exists.

## Baselines

- `python audit.py`: 40/40 checks, 0 errors, 0 warnings
- pytest: 2420 passed / 8 skipped (2428 collected)
- install-ledger: **1407/1407 Current, 0 drift** (rendered-file currency
  fix + artifact exclusion; config.json re-rendered via render-user-hooks)
- simplify-scan: **9 items** — unreferenced_def 0, except_pass 0,
  7 oversized files (#474), 2 fixture markers
- `overflow_path` adopted: silent-error-review scans full PostToolUse
  output (empirically verified field on 12.43)

## Calendar

Closeout event on `AGdevin` at 17:00 (id 8s8gac214l26k9ecl6nqb7h1mo).
