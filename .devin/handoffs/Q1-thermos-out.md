# Q1-thermos outcome

- Status: DONE
- Branch: `skill/thermos` in worktree `.worktrees/thermos`
- Commit: `b9ad532` `feat(skills): vendor cursor thermos review set + thermo subagents (MIT)`

## Files added (worktree)

- `skills/thermo-nuclear-code-quality-review/SKILL.md` - faithful vendor; description rewritten to "Use when" + attribution line
- `skills/thermo-nuclear-review/SKILL.md` - faithful vendor; description rewritten to "Use when" + attribution line
- `skills/thermos/SKILL.md` - adapted: Cursor `Task`/`subagent_type`/`run_in_background` replaced by `run_subagent(profile="reviewer", is_background=true)`, two parallel lanes then synthesize
- `agents/thermo-nuclear-review-subagent.md` - ported to bundle agent frontmatter (name, model swe-2-max, "Use for" description, read-only + exec verification-only allowed-tools)
- `agents/thermo-nuclear-code-quality-review-subagent.md` - same port

All five carry an MIT attribution line for cursor/plugins `thermos`. No em-dash chars in added prose; no AI signatures. manifest.json, README.md, TOOLS-MAP.md, and pre-existing skills/agents untouched.

## Verification (run inside worktree)

- `python audit.py` -> exit 0. Only expected stale-count items: agents not yet in manifest, TOOLS-MAP/README skills count stale (orchestrator reconciles).
- `python -m pytest -q tests/validation/test_skill_format_passes.py` -> 2 passed.

## Notes

- Upstream cloned via `git clone --depth 1` of github.com/cursor/plugins to temp dir.
- Nothing pushed; main checkout untouched.
