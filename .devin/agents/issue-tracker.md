# Issue tracker: Local Markdown

Issues and specs for this repository live under `.devin/scratch/`.

## Conventions

- One effort per directory: `.devin/scratch/<effort-slug>/`.
- The specification is `.devin/scratch/<effort-slug>/spec.md`.
- Tickets are separate files at `.devin/scratch/<effort-slug>/issues/<NN>-<slug>.md`.
- Number tickets from `01`.
- Record triage state with a `Status:` line near the top.
- Append discussion under `## Comments`.

## Operations

- Publish: create the appropriate file under the effort directory.
- Fetch: read the referenced ticket path.
- Map: use `.devin/scratch/<effort-slug>/map.md`.
- Block: record dependencies with `Blocked by: NN, NN`.
- Claim: set `Status: claimed` before work.
- Resolve: append `## Answer`, set `Status: resolved`, and update the map.
