# Goals (`.devin/goals/*.md`)

Macro-level goal tracking (issue #420). One file per goal; the
roadmap board rolls them up read-only — no OKR suite, no writes.

## Format

```markdown
# Goal: <title>

Status: active | done | archived
Horizon: <free text, e.g. 2026-11-09..2026-11-15>
Objective: <one line>
Efforts: <effort-slug> <effort-slug>     # scores all issues in group
Issues: <key> <group/key>                # scores explicit issue keys
Refs: #346 #417                          # traceability only, never scored
```

- `Efforts:` matches `group` names (scratch effort dirs / `.devin/issues`).
- `Issues:` matches issue keys; `group/key` disambiguates collisions.
- `Refs:` holds external pointers (GitHub issues/PRs) for traceability.
- Coverage = done/linked over resolvable local issues; `unresolved`
  lists link tokens that matched nothing (reported, not scored).
- Fields tolerate the same bold/dash variants as issue frontmatter.

Board output: `goals[]` in `--json`, `## Goals` table in markdown.
`README.md` itself is not treated as a goal.
