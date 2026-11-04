# Q2 best-practices vendoring: DONE

- Branch: `skill/best-practices` in worktree `.worktrees/best-practices`
- Commit: `0a18198 feat(skills): vendor unslop, typescript + vercel react best-practices (MIT)`
- No push, no main-checkout changes.

## Vendored

- `skills/unslop/SKILL.md` from cursor/plugins pstack (MIT, (c) Lauren Tan).
  Description extended with "Use when editing or reviewing prose to remove AI
  writing patterns." Attribution line appended.
- `skills/typescript-best-practices/` from cursor/plugins pstack (MIT,
  (c) Lauren Tan). SKILL.md plus `references/patterns.md` (vendored so the
  `Examples:` link resolves). Both cross-references to
  `principle-type-system-discipline` and `principle-boundary-discipline`
  replaced with one-line inline summaries in both files. Attribution appended.
- `skills/vercel-react-best-practices/` full dir from
  vercel-labs/agent-skills `skills/react-best-practices` (MIT, upstream name
  kept). Description rewritten "This skill should be used when" -> "Use when".
  Attribution line appended.
- All three frontmatter descriptions contain "Use when". No em-dash in added
  prose. No changes to manifest.json, README, TOOLS-MAP, or existing skills.

## Verification

- `python audit.py`: 6 errors, all stale-count class (manifest mismatch,
  skill_count, README/badge/TOOLS-MAP counts) expected because manifest and
  docs are out of scope. Warnings: pre-existing live!=bundle drifts.
- `pytest -q tests/validation/test_skill_format_passes.py`: 2 passed.

## Notes

- `references/patterns.md` was vendored alongside the TypeScript SKILL.md
  (upstream file the skill points to); its two principle-skill references were
  inlined the same way.
