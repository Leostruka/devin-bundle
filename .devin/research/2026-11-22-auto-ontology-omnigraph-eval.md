# Eval: NVIDIA auto-ontology + Omnigraph vs bundle knowledge surfaces

Issue: #700. Source: `.devin/research/2026-11-18-yt-batch5-reels11-survey.md` T3.
Date: 2026-11-22. Scope: assess-and-decide, not implement.

## Candidates

### NVIDIA auto-ontology (GH trending #1, Apache)

Reads DB schemas / samples / query history -> builds a business-term
dictionary -> human certifies -> agent consults the dictionary before
writing SQL. Backends: Postgres/Snowflake/Databricks/DuckDB via
MCP/CLI/API.

Bundle analog: `data-analyst` Step 1b already implements the core
pattern - `.devin/db-glossary.md` holds SQL-ready term definitions
with a `certified_by` column; new terms enter only after user
confirmation, corrections persist, and the glossary is consulted
before query formulation. The certify-then-consult loop exists.

- Gap (narrow): only auto-derivation is missing - mining query
  history/logs for candidate terms instead of growing the glossary
  interactively. A bounded version fits the bundle: a script that
  mines an MCP datasource's query log into glossary CANDIDATES for
  human certification (the certification step stays human; that is
  the correctness property, not a limitation).
- Verdict: PATTERN ALREADY IMPLEMENTED; residual = history-mining
  script, DEFERRED until a real MCP datasource exists to validate
  against (no held-out set today). No SKILL.md change needed - the
  pattern is documented and operational.

### Omnigraph (open-source, Roman Pronskiy)

Graph DB for agent world models: typed ontology enforced at write time,
per-agent branches + PR-style review/merge, git-like commits/rewind,
hybrid keyword+vector+graph query, S3-compatible open format.

Bundle analog: `structured-knowledge-extraction` already provides the
core invariants locally - typed versioned JSON graph under `.devin/`,
evidence+provenance per fact, merge with conflict reporting,
deterministic no-LLM lexical baseline. `knowledge-modeling` supplies
the ontology/validation discipline.

- Overlap: write-time type enforcement + merge/conflict semantics are
  already covered without a running DB.
- Gap: vector/hybrid retrieval and multi-agent branch/merge at scale.
  Real, but only materializes when the graph outgrows lexical search -
  no evidence of that scale in this workspace today.
- Verdict: MONITOR, DO NOT ADOPT. The S3-format graph DB is infra
  weight (service + storage) against the bundle's no-deps baseline;
  revisit if `.devin/` graph queries become a measured bottleneck.
  Recorded in `structured-knowledge-extraction`'s eval notes by this
  doc.

## Decision summary

| Candidate | Verdict | Action |
|---|---|---|
| NVIDIA auto-ontology | already implemented (Step 1b); mining deferred | none now; candidate extractor script when a datasource exists |
| Omnigraph | monitor | none; lexical `.devin/` graph covers current scale |
