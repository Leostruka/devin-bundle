---
name: writing-skills
description: Use when creating new skills, editing existing skills, verifying skills work before deployment, or when creating/editing any document an agent must read (`.devin/global_rules.md`, `.devin/rules/*.md`, docs reached by pointer).
triggers: [user, model]
---

# Writing Skills

**Writing skills IS TDD applied to process documentation.** Write test cases
(pressure scenarios with subagents), watch them fail (baseline), write the
skill, watch agents comply, refactor (close loopholes). If you didn't watch
an agent fail without the skill, you don't know it teaches the right thing.

Full creation workflow: `modes/creation.md`. Agent-facing doc principles:
`reference/writing-for-agents.md`. Frontmatter/invocation mechanics:
`reference/SKILL-MECHANICS.md`. Subagent pressure-testing:
`reference/testing-skills-with-subagents.md`. Persuasion:
`reference/persuasion-principles.md`. Graphviz conventions + renderer:
`reference/graphviz-conventions.dot`, `reference/render-graphs.js`.
Examples: `reference/examples/`.

## Essentials

- Personal skills: `~/.config/devin/skills/<name>/` (`%APPDATA%\devin\skills\`
  on Windows). Project skills: `.devin/skills/<name>/`. `.agents/skills/` is
  the cross-runtime standard.
- A skill is a **reference guide for proven techniques** — not a narrative of
  how you solved a problem once.
- Frontmatter: `name` + `description` written as discovery triggers
  ("Use when…"), not workflow summaries. Optional: `allowed-tools`,
  `subagent`, `agent`, `model` (free variants only), `permissions`,
  `triggers`.
- Keep SKILL.md small (~<10KB); push detail behind pointers
  (`reference/*.md`) — progressive disclosure protects the hierarchy.

## Context pointers (the triggering layer)

A pointer's *wording* decides when material gets reached. Front-load the
leading word; one trigger per branch (synonyms = one branch twice); cut
identity the body carries. Always-loaded pointer text spends context every
turn — prune harder than the body.

## The two loads

- **Context load** — always-loaded material costs tokens/attention every turn.
- **Cognitive load** — the human index of which docs exist. Spend where human
  judgement matters; remove elsewhere.

## Information hierarchy

1. In-file steps (primary) → 2. in-file reference → 3. disclosed reference
   (separate file behind a pointer). Inline what every branch needs; disclose
   what only some branches reach.

## Quality checklist (before commit)

- `name`/`description` per spec; discovery keywords in description.
- Devin-native tools and paths only; no non-Devin platform leakage.
- Subagent profiles per Rule 20 (`researcher`, never `subagent_explore`).
- Python for cross-platform helper scripts.
- No AI signatures.
- Pressure-tested with subagents where compliance matters.
