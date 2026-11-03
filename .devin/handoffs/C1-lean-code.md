# Contract C1: `lean-code` skill (Ponytail port)

- Role: `implementer`
- Lane: worktree `D:\Programing\ai_workspace\devin-bundle\.worktrees\lean-code`, branch `skill/lean-code`
  - setup: `git worktree add .worktrees/lean-code -b skill/lean-code` (run from repo root)
  - teardown: none (orchestrator merges)
- Objective: port the Ponytail minimal-code discipline into a new bundle skill.
- Source: `github.com/DietrichGebert/ponytail` (MIT). Fetch `skills/ponytail/SKILL.md`
  via raw.githubusercontent.com, port it with a one-line attribution comment.
- Output:
  - `skills/lean-code/SKILL.md` in the worktree. Frontmatter: `name: lean-code`,
    description containing "Use when". Body: the decision ladder (need it? in
    codebase? stdlib? platform? dependency? one line? then minimum + one small
    test for risky logic), the never-cut guardrails (validation, error handling,
    security, accessibility), and a short review/audit pointer section.
  - Do NOT edit manifest.json, README.md, or TOOLS-MAP.md (orchestrator reconciles).
- Boundaries: no AGENTS.md edits, no new scripts, no other paths. No AI
  signature, no em-dash in prose.
- Termination: max 20 turns.
- VFs (run inside worktree): `python audit.py` exits 0 on the skill check;
  `python -m pytest -q tests/validation/test_skill_format_passes.py` green.
- Report: `.devin/handoffs/C1-lean-code-out.md` with files touched + VF output.
