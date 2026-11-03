# C1 lean-code skill port

## Outcome

Created `skills/lean-code/SKILL.md` in worktree `.worktrees/lean-code` on
branch `skill/lean-code`, commit `a533332`
(`feat(skills): lean-code skill (Ponytail minimal-code port, MIT)`).

Source: MIT-licensed `ponytail` skill, fetched from
`https://raw.githubusercontent.com/DietrichGebert/ponytail/main/skills/ponytail/SKILL.md`.
Ported (not copied): Ponytail-specific levels/commands (`/ponytail lite|full|ultra`,
session mode, `argument-hint`) dropped; decision ladder, never-cut guardrails,
shortcut-comment convention, and one-small-test rule preserved. Attribution
comment included in the file.

## Files created

- `skills/lean-code/SKILL.md` (57 lines)

No other paths modified. manifest.json, README.md, .devin/docs/TOOLS-MAP.md,
AGENTS.md untouched per contract.

## Verification outputs

### `python audit.py`

- Process exit code: 0
- Summary: `Errors: 6, Warnings: 6`
- All 6 errors are stale skill counts in contract-forbidden files, flagged
  because the new skill raises the on-disk count to 156:
  - Manifest mismatch / manifest skill_count mismatch
  - README count wrong: 156 skills
  - README skills badge wrong (expected skills-156)
  - TOOLS-MAP.md skills count stale: expected 156 skills
  - README.md diagram skills count stale: expected 156 skills
- Warnings pre-existing or environmental: 4 live-vs-bundle skill hash drifts,
  missing v3.18.0 tag, changelog check skipped (dubious-ownership git error).

### `python -m pytest -q tests/validation/test_skill_format_passes.py`

- `2 passed in 0.56s`, exit code 0

## Notes

- Git required `-c safe.directory=<worktree>` per command (dubious ownership
  on this filesystem); no global config changed.
- Count-sync updates for manifest/README/TOOLS-MAP belong to a lane allowed to
  edit those files.
