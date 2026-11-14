# Local work tracker

Create one directory per effort. Follow `.devin/agents/issue-tracker.md`.

**Convention:** never commit loose files at the scratch root. Every artifact belongs in a `NN-slug/` or `<task>/` subdirectory. Shared subdirectories in use: `probes/`, `gate-scripts/`, `prompt-specs/`, `notes/`, `tools/` (legacy one-offs from earlier rounds).

## Status

Each subdirectory is an archived or pending effort. If an effort is no longer active, append `ARCHIVED` to its README or stub.

### Current stubs

- `akita-harness-loop-simplification` — archived idea stub.
- `devin-cli-3000.6.14-alignment` — archived alignment notes.
- `modular-atomic-action-modes` — archived design stub.

Completed efforts carry `Status: ARCHIVED` in their own README.md;
`roadmap-board.py` excludes them from the live frontier. Sweep
2026-11-08 archived: audit-r1..r6, reels-2..5, computer-use-staged-upgrades,
agentcraft-rts(+v2), general-audit, 3d_sources, cu-perception, cu-realtime.
