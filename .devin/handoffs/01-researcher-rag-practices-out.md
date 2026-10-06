# Handoff doc

## Header

- **Handoff**: 01-researcher-rag-practices
- **From role**: researcher
- **To role**: orchestrator (downstream: skill writer / domain)
- **Date**: 2026-10-05
- **ESCALATE**: none (worker note: researcher profile is read-only; report
  was persisted verbatim by the orchestrator)
- **CONSULT**: none

## Inputs consumed

- `.devin/vision.md` - scope, NFR-1/NFR-2 (offline-first, provider-neutral), boundaries
- `.devin/plans/2026-08-29-hyper-extract.md` - lexical-baseline-first direction (pt; matches tier model)
- `skills/knowledge-modeling/SKILL.md` - provenance convention (source file:line), lexical baseline precedent
- `skills/memory-management/SKILL.md` - memory-mode evidence pattern, arXiv:2608.15008
- `skills/writing-skills/SKILL.md` - progressive disclosure, ~10KB cap the research must serve
- `skills/context-hygiene/SKILL.md` - cost guards, "grep is cheaper" stance
- `skills/project-orchestrator/reference/research-protocol.md` - PRISMA-lite format

## Outputs produced

- `.devin/research/rag-practices.md` - full PRISMA-lite report: 24 queries, 36 mapped claims, tier model, self-quiz, residual gaps
- This handoff doc

## Decisions taken

- Tier model has four rungs (0 agentic-lexical, 1 BM25 index, 2 local hybrid, 3 hosted) rather than the contract's three - tier 0 is evidence-justified (C24/C26/C28) and matches the vision's "lexical-offline first" plus the repo's own grep-first culture.
- Vendor claims (Anthropic contextual-retrieval numbers, Elastic hybrid post, bm25s benchmarks) kept but flagged `[vendor]` with lateral reading noted - never sole support for a default.
- No vendor named as default anywhere; hosted options listed as a set, per contract boundary.

## Verified claims

- 36 claims mapped with `claim -> source -> verification`; grep `-> http` yields 30+ lines. Highlights:
  - Chunking strategy matters more than embedding model (Chroma report; direction corroborated independently) -> https://www.trychroma.com/research/evaluating-chunking
  - BM25 is a defensible scalable default: overtakes agentic file exploration ~10M corpus tokens -> https://arxiv.org/html/2607.26497v2
  - Tuned BM25 in agentic loop beat dense-retriever agents (83.1% BrowseComp-Plus) -> https://www.alphaxiv.org/abs/2605.10848
  - Index-free ripgrep retrieval ≈ graph-based RAG for repo code completion -> https://dl.acm.org/doi/abs/10.1145/3832136
  - Zero-dep BM25 exists in stdlib reach: SQLite FTS5 `bm25()` -> https://www.sqlite.org/fts5.html
  - RRF (k=60) unsupervised fusion beats individual systems -> https://cormack.uwaterloo.ca/cormacksigir09-rrf
  - Bi-encoder top-100 → cross-encoder rerank top-k is the standard pattern -> https://bge-model.com/bge/bge_reranker.html
  - RAGAS reference-free metrics family -> https://arxiv.org/abs/2309.15217 ; LLM judges need human references -> https://arxiv.org/abs/2503.05061
  - Seven RAG failure points catalog -> https://arxiv.org/abs/2401.05856
  - Retrieved-chunk count is inverted-U; >64k context degrades most models -> https://arxiv.org/html/2409.01666 , https://arxiv.org/pdf/2411.03538
  - Retrieval below a precision threshold harms coding agents -> https://arxiv.org/pdf/2608.05886

## Open items / gaps

- C29 (arXiv:2608.15008, excessive retrieval harms agentic tasks) cited via `memory-management` only - fetch paper before the skill cites it.
- sqlite-vec IVF/DiskANN marked alpha in secondary source - re-check before recommending beyond brute-force scale.
- License column for server-tier DBs (Qdrant/Weaviate/Elastic-vs-OpenSearch) rests on one secondary source - re-verify if skill names products.
- No verified numeric escalation thresholds; skill should teach "measure with golden set" rather than constants.
- Frozen-input hashes not re-verified in-lane (no exec tool); orchestrator re-runs at verify.

## Requested next action

- Orchestrator: re-run VF1–VF5, then hand `.devin/research/rag-practices.md` path + this doc to the skill writer. Skill should encode: tier ladder + escalation-by-measurement, golden-set eval first, structure-aware chunking default, RRF+rerank recipe at tier 2, failure-mode checklist, provenance convention. Explicitly omit: vendor defaults, model-of-the-month names, shipped runtime, MCP, implementation code.
