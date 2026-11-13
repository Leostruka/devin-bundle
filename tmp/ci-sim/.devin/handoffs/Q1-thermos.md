# Contract Q1: vendor+adapt Cursor `thermos` review set

- Role: `implementer`
- Lane: `git worktree add .worktrees/thermos -b skill/thermos` from repo root
  `D:\Programing\ai_workspace\devin-bundle`; work inside the worktree.
- Upstream (MIT (c) Cursor): `cursor/plugins` repo, `thermos/` plugin:
  - `thermos/skills/thermo-nuclear-code-quality-review/SKILL.md`
  - `thermos/skills/thermo-nuclear-review/SKILL.md`
  - `thermos/skills/thermos/SKILL.md`
  - `thermos/agents/thermo-nuclear-review-subagent.md`
  - `thermos/agents/thermo-nuclear-code-quality-review-subagent.md`
  Fetch via `git clone --depth 1` to a temp dir or raw.githubusercontent URLs.
- Output in worktree:
  - `skills/thermo-nuclear-code-quality-review/SKILL.md`: faithful vendor.
  - `skills/thermo-nuclear-review/SKILL.md`: faithful vendor.
  - `skills/thermos/SKILL.md`: adapt orchestration, replace Cursor replace Cursor
    `Task`/`subagent_type`/`run_in_background` mechanics with ours:
    `run_subagent(profile="reviewer", is_background=true)` two lanes in
    parallel, then synthesize (findings first, dedupe, weight overlaps,
    keep brief). Keep upstream wording where mechanics allow.
  - `agents/thermo-nuclear-review-subagent.md` and
    `agents/thermo-nuclear-code-quality-review-subagent.md`: port to our
    agents/ frontmatter format (match `agents/reviewer.md` shape:
    name, model `swe-2-max`, description with "Use for", allowed-tools
    list read-only + exec verification-only).
  - Each vendored file: one short line noting MIT source
    (cursor/plugins thermos). No em-dash chars in added prose.
  - Do NOT touch manifest.json, README.md, TOOLS-MAP.md, or any
    pre-existing skill/agent.
- VFs in worktree: `python audit.py` (only expected failures are the
  count/manifest mismatches orchestrator reconciles);
  `python -m pytest -q tests/validation/test_skill_format_passes.py` green.
- Commit on `skill/thermos`:
  `feat(skills): vendor cursor thermos review set + thermo subagents (MIT)`
- Report `.devin/handoffs/Q1-thermos-out.md`. Max 25 turns. Never push.
