## Summary

<!-- What does this PR change and why? -->

## Type

- [ ] feat — new feature
- [ ] fix — bug fix
- [ ] docs — documentation only
- [ ] refactor — code restructuring
- [ ] prune — removing dead/superseded content
- [ ] chore — maintenance

## Components affected

- [ ] AGENTS.md (rules)
- [ ] skills/
- [ ] agents/ (subagent profiles)
- [ ] hooks.v1.json
- [ ] scripts/ (hook Python scripts)
- [ ] config.json / mcp_config.json / credentials.toml
- [ ] install.ps1 / install.sh
- [ ] export.ps1 / export.sh
- [ ] manifest.json
- [ ] README.md / docs

## Verification

- [ ] `export.ps1 -DryRun` (or `export.sh --dry-run`) passes
- [ ] JSON files valid (`python -m json.tool <file>`)
- [ ] Python scripts compile (`python -m py_compile scripts/*.py`)
- [ ] Skill frontmatter valid (name matches dir, has description, starts with "Use when")
- [ ] No AI signatures in any file
- [ ] Manifest syncs with disk (`manifest.json` skills = `skills/` directories)
- [ ] CI passes

## Evidence

<!-- If this PR adds claims, numbers, or facts, cite the primary source. Per Rule 12, all claims must be verified against primary sources. -->
