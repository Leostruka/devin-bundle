# Contract Q2: vendor unslop + typescript + react best-practices

- Role: `implementer`
- Lane: `git worktree add .worktrees/best-practices -b skill/best-practices`
  from repo root `D:\Programing\ai_workspace\devin-bundle`.
- Upstream (all MIT):
  - `pstack/skills/unslop/SKILL.md` (cursor/plugins, (c) Lauren Tan)
  - `pstack/skills/typescript-best-practices/SKILL.md` (same)
  - `skills/react-best-practices/` from `vercel-labs/agent-skills`
    (frontmatter name `vercel-react-best-practices`, license MIT; copy
    the whole skill dir contents, not just SKILL.md)
- Output in worktree:
  - `skills/unslop/SKILL.md`: vendor it. Ensure frontmatter description
    contains "Use when" (extend the upstream one minimally if absent).
  - `skills/typescript-best-practices/SKILL.md`: vendor it. Upstream
    references principle skills (`type-system-discipline`,
    `boundary-discipline`): fetch those two
    `pstack/skills/principle-*/SKILL.md` files and replace each
    cross-reference with a one-line inline summary so the skill is
    self-contained in our bundle.
  - `skills/vercel-react-best-practices/`: vendor the upstream dir
    contents as-is (SKILL.md + any reference files); keep upstream name.
  - Attribution line per skill. No em-dash in added prose.
  - Do NOT touch manifest.json/README/TOOLS-MAP or existing skills.
- VFs: `python audit.py` (only stale-count errors);
  `pytest -q tests/validation/test_skill_format_passes.py` green.
- Commit on `skill/best-practices`:
  `feat(skills): vendor unslop, typescript + vercel react best-practices (MIT)`
- Report `.devin/handoffs/Q2-best-practices-out.md`. Max 25 turns.
