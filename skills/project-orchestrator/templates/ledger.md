# Ledger skeleton

Saved as `.devin/ledgers/<project>.md` in the target project. Append-only:
lines are added, never rewritten. Survives compaction; trust it over memory.

```markdown
# Ledger: <project>

## Task Ledger (what is true)

- Facts: <decisions, constraints, verified claims>
- Plan: <phase route, current phase>
- Roster: <active roles and their lanes>
- Dependency map: <Blocked by: edges between work items>
- Budget: <fan-out cap per phase>

## Progress Ledger (what is proven)

- <YYYY-MM-DD> <gate>: <status> | evidence: <command + result / artifact path>
- <YYYY-MM-DD> <contract ID>: <status> | evidence: <report path, VF results>
```

## Rules

- One line per gate or contract outcome, with evidence attached.
- A ticked gate without evidence is worse than an open one.
- On compaction: rebuild context from Task Ledger + last Progress lines.
