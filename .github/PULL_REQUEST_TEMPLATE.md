## Summary

<!-- What does this PR change and why? -->

## Linked issue

<!-- Required. Use `Closes #N` when this PR completes the issue (GitHub auto-closes it on merge). Use `Refs: #N` for partial or related work. The pr-quality workflow enforces this link. -->
Closes #

## Type

- [ ] feat - new feature
- [ ] fix - bug fix
- [ ] docs - documentation only
- [ ] refactor - code restructuring
- [ ] prune - removing dead/superseded content
- [ ] chore - maintenance

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
- [ ] .github/ (templates, workflows, release/dependabot config)

## Architectural context & trade-offs

<!-- Decisions made, alternatives rejected, and constraints honored. Link ADRs or plans when they exist (file path or `Refs: #N`). Delete this section only when the change is trivial. -->

## Verification

- [ ] `export.ps1 -DryRun` (or `export.sh --dry-run`) passes
- [ ] JSON files valid (`python -m json.tool <file>`)
- [ ] Python scripts compile (`python -m py_compile scripts/*.py`)
- [ ] Skill frontmatter valid (name matches dir, has description, starts with "Use when")
- [ ] No AI signatures in any file
- [ ] No em/en dashes in new or modified prose
- [ ] Manifest syncs with disk (`manifest.json` skills = `skills/` directories)
- [ ] Commits follow the issue-612 density template when applicable (`type(scope): subject (#N)` with Contexto e Motivacao, Detalhamento Tecnico, Decisoes Arquiteturais e Trade-offs, Validacao, `Refs: #N`)
- [ ] Commits carry `Refs: #N` wiring to the tracking issue
- [ ] CI passes

## Evidence

<!-- If this PR adds claims, numbers, or facts, cite the primary source. Per Rule 12, all claims must be verified against primary sources. -->
