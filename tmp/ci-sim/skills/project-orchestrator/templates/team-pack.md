# Team pack

Exportable roster: aggregates a project's proven team design for reuse in
another project. Saved as `.devin/team-pack.md`. On import the orchestrator
reads it, resolves name conflicts, and instantiates `workers/<role>/`.

## Pack

- **Source project**: <name>
- **Exported**: <YYYY-MM-DD>
- **Methodology**: <RUP | Scrum | hybrid, per the development case>

## Roles

| Role | Base profile | Charter summary | Boundaries |
|---|---|---|---|
| <role> | <profile> | <one-line mandate> | <NOT-list> |

## Conventions

- <contract defaults worth keeping: termination limits, VF style,
  peer-consult caps, lane setup patterns>

## Import rules

- Name conflict with an existing `workers/<role>/`: rename or merge under
  orchestrator decision; record the resolution in the Progress Ledger.
- Charters import as drafts: adjust mandate and boundaries to the new scope
  before the first dispatch.
