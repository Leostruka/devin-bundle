---
name: project-bootstrap
description: Use when starting work on a project that lacks a `.devin/` configuration, when the user wants to add skills/hooks/rules/local tools systematically, when configuring a repo's issue tracker + triage labels + domain docs for the engineering skills, or when setting up Husky pre-commit hooks with lint-staged/typecheck/tests.
triggers: [user, model]
---

# Project Bootstrap

Three modes for preparing a repo for agent work. Full detail in
`modes/<mode>.md`; read it when you enter the mode.

| Mode | When | Detail |
|---|---|---|
| **Setup** | No/incomplete `.devin/` — rules, hooks, skills, memory, agent config | `modes/setup.md` |
| **Eng-skills** | Configure issue tracker, triage labels, `.devin/CONTEXT.md` + `adr/` layout | `modes/eng-skills.md` |
| **Pre-commit** | Husky + lint-staged + typecheck + tests on commit | `modes/pre-commit.md` |

Order: Setup first (creates `.devin/`), then Eng-skills (tracker + domain
docs), then Pre-commit. If `.devin/` is complete and the user wants a
specific edit → `devin-config` instead.

## Shared principles

- Everything agent-facing lives inside `.devin/` only — nothing outside.
- Explore before writing: `git remote -v`, stack signals (package.json,
  pyproject.toml, Cargo.toml, go.mod), existing `.devin/` contents.
- Confirm with the user before writing config; prompt-driven, not scripted.
- Nothing gets committed without a green check where the repo has one.

## Key conventions

- Rules: `.devin/global_rules.md` + `.devin/rules/*.md` (trigger-scoped; glob/always_on/manual frontmatter — templates in `templates/`).
- Skills: `.devin/skills/<name>/SKILL.md`.
- Hooks: `.devin/hooks.v1.json` (project-level) or rendered into user config.
- Issue tracker: GitHub default, local markdown supported —
  `reference/issue-tracker-*.md`, `reference/triage-labels.md`,
  `reference/domain.md`.
- Agent template: `templates/agents.md`.

## Cross-skills

- `devin-config` — wiring project `config.json`, hooks, and permissions after scaffolding.
- `mcp-governance` — auditing/adding MCP servers for the new project (tool-count cost, trust review).
