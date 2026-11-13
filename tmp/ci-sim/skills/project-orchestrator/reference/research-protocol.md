# Research protocol

Runs inside gate G2, before any technology or architecture decision, and
again whenever a critical claim needs grounding. Execution is delegated to
the `researcher` profile (read-only, free). Output: one file per area at
`.devin/research/<area>.md`.

## PRISMA-lite

Every research file declares, at the top:

- **Criteria**: what counts as an acceptable source (primary docs, specs,
  first-party benchmarks) and what is excluded, with justification
- **Queries**: the exact queries run, in order
- **Coverage**: areas searched vs areas deliberately skipped

## Claim mapping

Every load-bearing claim in the research output maps to its source:

```
claim -> source URL/path -> verified (existence, entailment)
```

- **Existence**: the source exists and says something on the topic.
- **Entailment**: the source actually supports the claim as written, not a
  weaker or different claim.

## Lateral reading

Never evaluate a source by its own claims. For critical sources (the ones a
decision depends on), leave the page: check who publishes it, what
independent sources say about it, and whether the claim survives outside
the source's own site. Vendor benchmarks and docs blogs get this treatment
by default.

## Self-quiz (coverage audit)

Before a stack or architecture proposal leaves G2, answer in the research
file:

1. Which decision does each verified claim support?
2. Which decision lacks a verified claim? (gap list)
3. Which claims rest on a single source?
4. What would change the recommendation?

A proposal with an empty gap list is suspect; record real residual gaps or
state explicitly that none remain.

## Handoff

Research feeds the `domain`/`architect` roles via `handoff-doc.md`: the
worker receives the file path, the verified claim list, and the open gaps.
It never receives a pasted research dump in the dispatch prompt.
