# Ledger skeleton

Saved as `.devin/ledgers/<project>.md` in the target project. Append-only:
lines are added, never rewritten. Survives compaction; trust it over memory.

```markdown
# Ledger: <project>

## Status (rewritten each event; the only non-append-only section)

- Phase: <current gate>
- Active roster: <roles + lanes + handles>
- Escalations open: <list or "none">

## Task Ledger (what is true)

- Facts: <decisions, constraints, verified claims>
- Plan: <phase route, current phase>
- Roster: <active roles and their lanes>
- Advisor: <peer sid + session id, or "in-session agent_id", or "off">
- Dependency map: <Blocked by: edges between work items>
- Budget: <fan-out cap per phase; advisor consults per phase>
  - consumed: <turns>/<minutes> accumulated per phase

## Progress Ledger (what is proven)

- <YYYY-MM-DD> <gate>: <status> | evidence: <command + result / artifact path>
- <YYYY-MM-DD> <contract ID>: <status> | handle: <agent_id|sid> |
  spent: <turns>/<min> | evidence: <report path, VF results>
```

## Rules

- One line per gate or contract outcome, with evidence attached.
- `## Status` is the single exception to append-only: rewrite it on every
  event so the user reads swarm state in one place.
- A ticked gate without evidence is worse than an open one.
- On compaction: rebuild context from Task Ledger + last Progress lines.
