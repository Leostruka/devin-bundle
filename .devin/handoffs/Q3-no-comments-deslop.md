# Contract Q3: port `no-comments` + build `de-slop` composite

- Role: `implementer`
- Lane: `git worktree add .worktrees/de-slop -b skill/de-slop`
  from repo root `D:\Programing\ai_workspace\devin-bundle`.
- Upstream (MIT, cursor/plugins pstack, (c) Lauren Tan):
  `pstack/skills/no-comments/SKILL.md` + `pstack/agents/comment-sicko.md`.
- Output in worktree:
  - `skills/no-comments/SKILL.md`: PORT, not verbatim. Upstream spawns
    a `comment-sicko` Task subagent and references poteto-mode, `/how`,
    `/why`, `/architect`. Map to our bundle: spawn
    `run_subagent(profile="reviewer")` with the comment-sicko rubric
    inlined in the delegation prompt (extract the rubric from
    `agents/comment-sicko.md` and embed it as a prompt template inside
    the skill); replace `/how` `/why` `/architect` calls with "delegate
    to `architect`/`researcher` profiles or ask the user". Keep the
    workflow: scoped diff -> hunt -> accept/reject rubric -> smallest
    root-cause fix -> constraint comments get type/test/lint encodings
    -> report counts. Attribution line, no em-dash.
  - `skills/de-slop/SKILL.md`: NEW composite skill implementing the
    reel's pattern: one pass that sequences the bundle's simplification
    skills on the current diff/branch before PR:
    1) `lean-code` minimal-code sweep,
    2) `no-comments` comment-smell pass,
    3) `unslop` on changed prose/docs,
    4) `thermo-nuclear-code-quality-review` structural pass
       (or `thermos` for the dual review),
    5) optional `typescript-best-practices` /
       `vercel-react-best-practices` when the diff touches .ts/.tsx/React.
    Document: run order, "multi-pass" guidance (a second run catches
    more due to non-determinism, per the reel), stop conditions (no
    new findings / diff frozen), and that each invoked skill's own
    rules still govern. Frontmatter description with "Use when",
    e.g. before opening a PR, when asked to simplify/de-slop a diff.
  - Do NOT touch manifest.json/README/TOOLS-MAP or other skills.
- VFs: `python audit.py` (only stale-count errors);
  `pytest -q tests/validation/test_skill_format_passes.py` green.
- Commit on `skill/de-slop`:
  `feat(skills): no-comments port + de-slop composite pass`
- Report `.devin/handoffs/Q3-no-comments-deslop-out.md`. Max 25 turns.
