---
name: issue-tracker
model: swe-2-flash-medium
description: Use when reading, creating, claiming, or resolving local Markdown issues for this repository.
allowed-tools:
  - read
  - write
  - edit
  - grep
  - glob
  - find_file_by_name
---

# Issue tracker: Local Markdown

Issues and specs for this repository live under `.devin/scratch/`.
Decision record: `.devin/adr/007-scratch-issue-tracker.md`.
`.devin/scratch/<effort>/` holds per-effort work items;
`.devin/issues/` holds milestone- and design-level issues
(`ISSUE_*`, `MILESTONE_*`). GitHub Issues is the external intake only.

## Conventions

- One effort per directory: `.devin/scratch/<effort-slug>/`.
- The specification is `.devin/scratch/<effort-slug>/spec.md`.
- Tickets are separate files at `.devin/scratch/<effort-slug>/issues/<NN>-<slug>.md`.
- Number tickets from `01`.
- Record triage state with a `Status:` line near the top.
- Timeboxing (issue #418): estimate work in minutes with an
  `estimate_min: <int>` field near the top; record effort spent with
  `actual_min: <int>` when resolving. The roteiro planner consumes
  `estimate_min` as the task `minutes` when packing the day.
- Append discussion under `## Comments`.

## Operations

- Publish: create the appropriate file under the effort directory.
- Fetch: read the referenced ticket path.
- Map: use `.devin/scratch/<effort-slug>/map.md`.
- Block: record dependencies with `Blocked by: NN, NN`.
- Claim: set `Status: claimed` before work.
- Resolve: append `## Answer`, set `Status: resolved`, and update the map.
- Focus sessions (issue #419): `python scripts/focus.py start
  --issue <KEY> [--effort <slug>]` before a work block, `stop` after,
  `report [--day YYYY-MM-DD] [--json]` for per-day/per-issue focus
  minutes. Ledger: `.devin/ledgers/focus.jsonl` (gitignored).
