---
trigger: glob
globs:
  - ".devin/**"
description: Conventions for editing this project's .devin/ configuration
---

# .devin/ conventions

- Agent-facing files live inside `.devin/` only — nothing outside.
- Rules: `.devin/global_rules.md` (always-on) + `.devin/rules/*.md` (trigger-scoped). `globs:` frontmatter is a YAML sequence, not a string.
- Skills: `.devin/skills/<name>/SKILL.md` with `name` + `description` frontmatter.
- Hooks: `.devin/hooks.v1.json` is the single source; do not hand-edit rendered hooks elsewhere.
- Memory and notes: `.devin/memory/`, `.devin/notes/` — plain text, project-scoped.
- Ledger before multi-step work: `.devin/ledgers/<task>.md` with CHECK/EXPECT/EVIDENCE gates.
