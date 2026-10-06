---
name: rag
description: Use when building retrieval over a project corpus (docs, code, notes), when answering chunking/embedding/vector-store questions, when evaluating whether retrieval actually works, or when an agent "can't find things in the docs" and grep alone is not cutting it.
triggers: [user, model]
---

# RAG

Build retrieval over arbitrary project corpora, offline-first and
provider-neutral. Evidence base: `.devin/research/rag-practices.md` (claims
cited as C-numbers); tier model: `.devin/adr/004-rag-skill-tier-model.md`.

## The tier ladder

Escalate only on **measured failure** of the current tier: golden-set
recall/hit-rate misses, not vibes. Before tiering up, re-run the eval on
the current tier - lexical tiers are stronger than assumed.

| Tier | Retrieval | Deps | Escalate when |
|---|---|---|---|
| 0 - Agentic lexical | glob/grep/read loops over the live tree | none | corpus outgrows ad-hoc exploration; repeated identical queries |
| 1 - Lexical index | BM25 over chunked corpus (SQLite FTS5 `bm25()`, or a BM25 pip package) | stdlib or one pip pkg | paraphrase/synonym queries miss on the golden set |
| 2 - Local hybrid | local embeddings + in-process store + RRF fusion with BM25 + optional local cross-encoder rerank | opt-in deps | corpus/ops scale beyond local, or latency budget needs approximate indexes |
| 3 - Hosted / server | hosted embeddings or a server vector DB | consent + credentials | managed ops required; never the default |

Rationale: agentic filesystem exploration leads at small corpus scale but
costs far more query tokens; a BM25 index overtakes it as corpora grow
(C24). For code, index-free ripgrep-style retrieval matches graph-based
RAG baselines (C26), and a shipped coding agent uses live-tree ripgrep
search instead of a vector index (C28 [secondary]). A well-tuned BM25
retriever inside an agent loop can beat released dense-retriever agents
(C25 [abs]).

Detailed recipes per tier: `reference/tier-recipes.md`.

## Build order (all tiers)

1. **Golden set first.** Before any embedding or index work, write a
   golden set of query -> expected-passage pairs and measure hit rate /
   recall@k / MRR deterministically (C18). Retrieval below a precision
   threshold actively degrades a coding agent, not just wastes tokens
   (C27 [abs]).
2. **Structure-aware chunking.** Default: split on document structure
   (Markdown headers, code language separators), then recursive
   character splitting (`"\n\n" -> "\n" -> " "`) as the size cap (C2).
   Chunking choice has significant impact on retrieval accuracy and some
   popular defaults perform poorly (C3); the chunking delta can exceed
   the embedding-model delta, so fix splitting before swapping models
   (C4 [single-corpus]). No strategy fits all corpora (C1); semantic
   chunking improves cohesion at added cost and unpredictable sizes (C5).
3. **Provenance on every chunk.** Each stored chunk carries
   `path:start_line-end_line` plus enough text to quote it back, matching
   the `knowledge-modeling` extracted-fact convention. Retrieval that
   cannot cite where a chunk came from is not shippable here.
4. **Tier entry.** Start at tier 0. Add a BM25 index (tier 1) when the
   corpus is large or queries repeat; verify the target Python actually
   ships FTS5 compiled in - it is a build-time, platform-dependent option -
   before relying on `bm25()` (C36). Hybrid +
   rerank (tier 2) only when the golden set shows lexical misses on
   paraphrase; pick embedding models from MTEB filtered by domain - code
   retrieval tasks exist there - never by hype (C6).

Eval-harness sketch and metric definitions: `reference/eval-and-failures.md`.

## Failure-mode checklist

Walk this list before blaming the model (full catalog with C-numbers in
`reference/eval-and-failures.md`; the seven canonical failure points are
C34):

- Missing content: the answer is not in the corpus (C34).
- Missed top rank: present but retrieval never surfaces it - a recall
  problem, fixable by chunking/fusion, not generation (C34).
- Not consolidated: retrieved but lost among too many chunks - answer
  quality vs chunk count is an inverted U (C31); order best chunks at
  the beginning and end of context, mid-context is used worst (C33).
- Not extracted / wrong format / wrong specificity: prompt or
  post-processing issues, not index issues (C34).
- Stale or duplicated index entries drifting from the live tree (C34
  family) - rebuild or incremental-merge with conflict reporting.
- Too much retrieved context: accuracy degrades past large retrieved
  volumes in most models (C32 [abs]); retrieval is chosen over long
  context for cost, not quality (C30).
- Agentic-loop risks: compounding errors, memory poisoning, cascading
  tool failures - bound the loop (C23 [abs]).

## Agentic pattern

Retrieval-as-tool inside the reasoning loop is the current paradigm
(C22): the agent issues search calls, reads results, refines queries.
Agentic reasoning works best *after* ranked discovery, not in place of
it (C24). Keep loops bounded and apply context-hygiene cost guards.

## Teach vs omit

Teach: the tier ladder with measured escalation; golden-set eval before
embeddings; structure-aware chunking; provenance; hybrid + rerank recipe
at tier 2; staleness/dedup; the failure checklist.

Omit (project boundaries): vendor walkthroughs and hosted-service setup
(provider-neutral per vision); any named "best" embedding model (point
at MTEB - leaderboards churn); shipped runtimes, indexes, or MCP
configs; GraphRAG and retriever fine-tuning (construction cost, scope);
implementation code (this skill is guidance, not a runtime).
