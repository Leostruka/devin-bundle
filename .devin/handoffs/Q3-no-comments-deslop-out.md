# Q3 report: no-comments port + de-slop composite

**Status:** DONE

## Commits

- `26e3440` on `skill/de-slop` (worktree `.worktrees/de-slop`):
  `feat(skills): no-comments port + de-slop composite pass`
- Not pushed. Main checkout untouched.

## Delivered

- `skills/no-comments/SKILL.md`: port of pstack `no-comments` +
  `comment-sicko` (github.com/cursor/plugins, MIT, (c) Lauren Tan).
  Attribution in an HTML comment. `comment-sicko` Task agent remapped to
  `run_subagent(profile="reviewer")` with the rubric inlined as a fenced
  delegation-prompt template. `/how`, `/why`, `/architect` remapped to
  `researcher`/`architect` profiles or asking the user. Workflow kept:
  scoped diff -> hunt -> accept/reject rubric -> smallest root-cause fix ->
  type/test/lint encodings for constraint comments -> counts report.
- `skills/de-slop/SKILL.md`: new composite. Run order `lean-code` ->
  `no-comments` -> `unslop` -> `thermo-nuclear-code-quality-review`
  (or `thermos`) -> conditional `typescript-best-practices` /
  `vercel-react-best-practices`. Documents multi-pass guidance,
  stop conditions (no new findings / diff frozen), and that each invoked
  skill's own rules govern. Referenced skills that have not landed yet are
  named anyway per contract.
- Frontmatter: `name` + description containing "Use when" on both skills.
  No em-dashes (verified via `grep -n '—\|–'`, clean).
- No changes to manifest.json, README, TOOLS-MAP, or other skills.

## Verification

- `python audit.py` (in worktree): exit 0; only stale-count errors
  (README/TOOLS-MAP expect 162 skills, now 164). Warnings only otherwise.
- `python -m pytest -q tests/validation/test_skill_format_passes.py`:
  2 passed.

## Concerns

- Audit stale-count errors are expected per contract; counts go green once
  a counts/docs lane updates README/TOOLS-MAP/manifest.
- Git required `safe.directory` global config for the worktree path.
