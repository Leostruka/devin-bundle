# Project State - 2026-11-10 (improvement-loop snapshot)

## Position

Main `aebff80` (origin synced). CLI `3000.12.43` installed = latest;
bundle validated against it (`validated_cli_version` bumped in #457).

## Merged today (post-reels-7)

| PR | What |
|---|---|
| #458 | laya worker: `raw_runner_up_probability` (distribution OR probabilities keys) |
| #459 | simplify-scan precision: comments-only markers, annotated-pass, pytest-def skip (2612->149 items) |
| #460 | handoff skill: acp-summarizer 3-section schema (Overview/Breadcrumbs/Current State) |
| #461 | pulse: bold-colon Status/Blocked-by + status_vocab canonical statuses + archived-effort exclusion (168->75 phantom removal; real claimable = 0) |
| #462 | DRS blueprint spec draft (live verify platform-blocked) |
| #463 | laya margin evidence: runner-up recapture, margin gate rejected (#431 item 5) |
| #464 | CLI 12.43 compat doc: ACP modes + client fs-gateway verified |

Pending auto-merge: #465 (issue triage), #466 (simplify-scan sibling-reraise suppression).

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

- `python audit.py`: 0 errors; warnings only for <24h changelog-ref grace
- pytest: 2397 passed / 8 skipped (post-batch); targeted suites green since
- install-ledger: Modified=0 Foreign=0
- simplify-scan: 149 items -> 103 after sibling-reraise suppression (#466)

## Calendar

Closeout event on `AGdevin` at 17:00 (id 8s8gac214l26k9ecl6nqb7h1mo).
