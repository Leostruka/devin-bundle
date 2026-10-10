# ISSUE 07: Port audit, `mattpocock/skills` upstream → our bundle (agnostic)

Status: planned (research done) · Source: `github.com/mattpocock/skills` (MIT, aihero.dev/skills) · Ledger: `.devin/research/4_fronts_recon.md`

## Contexto & Valor

- Upstream inventory (verified via API):
  - `engineering/`: ask-matt, code-review, codebase-design, diagnosing-bugs, domain-modeling, grill-with-docs, implement-spec, implement, improve-codebase-architecture, pr, prototype, research, retro, setup-matt-pocock-skills, tdd, to-spec, to-tickets, triage, wayfinder, wizard.
  - `productivity/`: grill-me, grilling, handoff, teach, to-questionnaire, wait-what, writing-for-agents.
  - `misc/`: git-guardrails-claude-code, migrate-to-shoehorn, scaffold-exercises, setup-pre-commit.
- Large overlap with our set (code-review, codebase-design, diagnosing-bugs, domain-modeling, grilling, tdd, prototype, handoff, writing-for-agents, wayfinder, intake/triage...). Ours were likely seeded from this source and have drifted.
- Value: (a) refresh drifted skills from upstream improvements; (b) adopt genuinely new ones, candidates: `teach`, `wait-what`, `retro`, `grill-with-docs`, `to-questionnaire`, `wizard`, `scaffold-exercises`, `git-guardrails`; (c) do it **agnostically**: strip tool-specific refs (`.claude/`, claude-code hooks) so ports work for any agent CLI, per our `.devin/skills/` conventions.

## Brain (Skill)

- **Update in place** (Rule 3): for each overlap skill, diff ours vs upstream, port substantive deltas (new sections, better gates), keep our local adaptations (devin tool names, laya routing, hook wiring).
- **New ports** only where value is distinct: `teach` (explain concept at user level), `wait-what` (confusion interrupt), `retro` (post-task review), `grill-with-docs` (grill grounded in repo docs), `to-questionnaire` (planning mode exists, check mode overlap first).
- Gate: `writing-skills` checklist on every touched/new SKILL.md; `skill-discovery` routing updated.

## Muscle (Extension)

- None by default (skills are text). If a ported skill ships helper scripts (e.g. `setup-pre-commit`, `git-guardrails`), they land under the skill's own dir or `extensions/` per ADR-003 conventions, rewritten to Devin CLI hooks (`hooks.v1.json` + `scripts/*.py`), never `.claude/`.

## Step-by-step (on authorization)

0. Shallow-clone `mattpocock/skills`; enumerate SKILL.md files vs our `skills/` + `%APPDATA%\devin\skills`; produce `port_matrix.md` (same / diverged / new / skip-with-reason).
1. For `same` rows: diff content, port deltas, record source commit hash in the file header comment for future re-sync.
2. For `new` rows: port agnostically (tool-neutral phrasing, our frontmatter format, our tool names).
3. For `skip` rows: record reason (duplicates our mode, tool-locked, low value).
4. Gate: `validate-skill-format.py` on every touched file; spot-run 1 ported skill end-to-end.
5. Update `ask-bundle`/`leo` routing table.

## Non-goals

No wholesale copy, no claude-specific imports, no new extensions unless a script genuinely needs a home, no skill deletions (Rule 25 analog: deprecations need approval).
