# Plan: quality-skills adoption (reel DePGBFXtswr) - 2026-11-03

Source: `.devin/research/2026-11-03-reel-quality-skills-survey.md`.
Scope: adopt the reel's quality/de-slop skill stack into the bundle.
Non-goals: no full pstack port, no poteto-mode port, no MERIDIAN work
(nothing investment-scope in this reel), no changes to `lean-code`
(already adopted via PR #293).

## Contracts

| ID | Deliverable | Role | Lane |
|----|-------------|------|------|
| C1 | `skills/thermo-nuclear-code-quality-review/`, `skills/thermo-nuclear-review/`, `skills/thermos/` + `agents/thermo-nuclear-*-subagent.md` (vendor+adapt, MIT Cursor) | implementer | `.worktrees/thermos`, branch `skill/thermos` |
| C2 | `skills/unslop/`, `skills/typescript-best-practices/`, `skills/vercel-react-best-practices/` (vendor, MIT) | implementer | `.worktrees/best-practices`, branch `skill/best-practices` |
| C3 | `skills/no-comments/` (port: comment-sicko -> reviewer subagent) + `skills/de-slop/` (new composite pass) | implementer | `.worktrees/de-slop`, branch `skill/de-slop` |
| C4 | `.devin/research/2026-11-03-pstack-backlog-eval.md` (remaining ~50 pstack + vercel extras eval table) | researcher | none |

Sequence: C1, C2, C3 in parallel (cap 3). C4 after first slot frees.
Reconcile: +8 skills (158 -> 166), +2 agents; orchestrator updates
manifest/README/TOOLS-MAP after merges.

## Per-contract VFs

- `python audit.py`: 0 errors after orchestrator reconcile
- `python -m pytest -q tests/validation/test_skill_format_passes.py`: green
- `python -m pytest -q tests/`: full gate before PR

## Boundaries (all lanes)

- Worktree lanes only; no main-checkout writes; no pushes.
- No em-dash in new prose; no AI signatures; attribution line per vendored file.
- Frontmatter: `name` + description containing "Use when".
- Subagent references in vendored Cursor skills must map to our
  `run_subagent` profiles (reviewer/researcher/implementer) and
  `agents/` profile format, not Cursor `Task`/`subagent_type` names.
- Orchestrator owns manifest.json, README.md, TOOLS-MAP.md, agents index.

## Final gate

audit 0 errors; full pytest green; branch `feat/quality-skills` -> PR ->
auto-merge squash; worktrees removed.
