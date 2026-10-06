# Research: RAG practices (verified base for the `rag` skill)

Contract: `01-researcher-rag-practices`. Track: agent-docs-rag.
Protocol: PRISMA-lite per `skills/project-orchestrator/reference/research-protocol.md`.
Date: 2026-10-05 (session date per `.devin/vision.md` intake record).

## Criteria

**Acceptable sources**, in descending strength:

1. Peer-reviewed papers and arXiv preprints with IDs (abstract-level
   entailment marked when only the abstract was read).
2. Official documentation / maintainer repos (SQLite, LangChain, FAISS wiki,
   sentence-transformers, BGE, LanceDB, PyPI pages).
3. Vendor engineering posts - accepted only when the claim is technical and
   reproducible, always flagged `[vendor]`; never sole support for a default.
4. Independent benchmarks/blogs - accepted as directional evidence, flagged
   `[secondary]`/`[single-corpus]`, never sole support.

**Excluded:** SEO listicles as sole evidence; benchmark numbers without a
stated dataset/protocol; claims recommending a specific hosted vendor as a
default (contract boundary: provider-neutral).

## Queries

Run in order via `web_search`:

1. `"Seven Failure Points" RAG retrieval augmented generation engineering paper arxiv`
2. `RAG chunking strategies benchmark comparison semantic recursive character splitting`
3. `MTEB leaderboard massive text embedding benchmark HuggingFace`
4. `RAGAS framework RAG evaluation metrics faithfulness context precision recall`
5. `hybrid search BM25 dense embeddings reciprocal rank fusion reranking cross-encoder`
6. `in-process embedded vector database sqlite-vec LanceDB FAISS comparison local`
7. `Anthropic contextual retrieval chunk embeddings BM25 reranking failure rate`
8. `agentic RAG survey iterative retrieval tool use LLM agents arxiv`
9. `BM25 vs dense retrieval code search agents grep sufficient study`
10. `RAG vs long context window comparison study Gemini "Retrieval Augmented Generation or Long-Context"`
11. `reciprocal rank fusion Cormack 2009 original paper "Outperforms" condorcet`
12. `LLM-as-a-judge evaluation limitations biases RAG evaluation golden dataset`
13. `SQLite FTS5 bm25 built-in ranking function documentation`
14. `sentence-transformers fastembed local embedding models BGE E5 all-MiniLM offline`
15. `Chroma "evaluating chunking strategies" research token size overlap findings`
16. `cross-encoder reranker bge-reranker jina reranker ms marco top-k candidates docs`
17. `Gao 2023 "Retrieval-Augmented Generation for Large Language Models" survey naive advanced modular arxiv`
18. `HyDE hypothetical document embeddings zero-shot dense retrieval arxiv 2212.10496`
19. `LangChain RecursiveCharacterTextSplitter markdown header splitter documentation`
20. `faiss library facebook research similarity search github IVF HNSW product quantization`
21. `rank_bm25 python package BM25Okapi pypi bm25s fast BM25 python`
22. `"2307.03172" OR "lost in the middle" language models long contexts retrieval position`
23. `lancedb/lancedb github embedded vector database official repository`
24. `Claude Code codebase search grep no embeddings vector database agentic search`

## Coverage

**Searched:** chunking strategies; embedding selection (local vs hosted);
vector stores (in-process vs server); hybrid retrieval + reranking; RAG
evaluation; agentic/tool-loop retrieval; failure modes; RAG-vs-long-context;
coding-agent search practice (grep vs index).

**Deliberately skipped:** GraphRAG/knowledge-graph indexing (heavy
construction; arXiv:2607.26497 shows construction walls before deploy scale);
multimodal/image embeddings (out of scope per vision - text/code corpora);
fine-tuning retrievers (beyond skill scope); specific vendor pricing (changes
fast; provider-neutral boundary); late chunking / ColBERT late interaction
(interesting but non-load-bearing for a tier-0..2 skill).

## Claim map

Format: `claim -> source -> verification (existence, entailment)`.
`[abs]` = abstract-level verification. `[vendor]` = vendor source, lateral
reading applied. `[secondary]` = independent non-primary source.

### Chunking

- **C1.** No single chunking strategy fits all corpora; the optimal strategy
  depends on document structure and content, and one-size-fits-all chunking is
  increasingly recognized as inadequate
  -> https://aclanthology.org/2026.lrec-1.903.pdf
  -> verified (existence, [abs] entailment; LREC 2026 paper)
- **C2.** Recursive character splitting (separator hierarchy
  `["\n\n","\n"," ",""]`, paragraph→sentence→word) is the recommended generic
  default; structure-aware splitters exist for Markdown headers, HTML, JSON,
  and per-language code separators
  -> https://docs.langchain.com/oss/python/integrations/splitters
  -> verified (existence, entailment; official LangChain docs)
- **C3.** Chunking-strategy choice has significant impact on retrieval
  accuracy and efficiency; `RecursiveCharacterTextSplitter` performs well when
  parameterized appropriately; some popular defaults perform poorly
  -> https://www.trychroma.com/research/evaluating-chunking
  -> verified (existence, entailment; Chroma technical report, Smith &
  Troynikov 2024)
- **C4.** On one 500-doc technical corpus, chunking-strategy delta (~0.10
  score) exceeded embedding-model delta (~0.04) - i.e., fix chunking before
  upgrading embeddings
  -> https://yoke-agent.digital/blog/benchmarking-chunking-strategies/
  -> verified existence; weak entailment - [single-corpus] independent blog;
  direction corroborated by C3, treat as hypothesis not law
- **C5.** Semantic chunking (embedding-based boundary detection) improves
  cohesion but adds computational cost and unpredictable chunk sizes
  -> https://aclanthology.org/2026.lrec-1.903.pdf
  -> verified ([abs]; also Chroma C3 evaluated ClusterSemanticChunker as
  competitive but not dominant)

### Embeddings

- **C6.** MTEB is the standard public benchmark for embedding selection:
  1000+ tasks, 1000+ languages, domain filters including code/legal/
  healthcare retrieval; leaderboard is interactive and filterable
  -> https://huggingface.co/mteb
  -> verified (existence, entailment; official MTEB org docs; paper
  https://arxiv.org/abs/2210.07316)
- **C7.** Local embedding models run offline with no API key: fastembed uses
  ONNX runtime, downloads model once then caches; sentence-transformers is the
  reference library with general-purpose `all-*` models
  (`all-mpnet-base-v2` best quality, `all-MiniLM-L6-v2` ~5x faster, 384-dim)
  -> https://github.com/qdrant/fastembed/blob/main/README.md
  -> verified (existence, entailment; official repos +
  https://github.com/UKPLab/sentence-transformers `pretrained_models.md`)
- **C8.** BGE-family local models (bge-small/base/large-en-v1.5, 384/768/1024
  dim) are common local defaults with quantized variants
  -> https://surrealdb.com/docs/build/integrations/embeddings-providers/fastembed
  -> verified (existence, entailment; model table mirrors fastembed's list)

### Vector stores

- **C9.** FAISS is an in-process C++/Python library (not a server) providing
  exact (Flat), IVF, PQ, and HNSW index families; index choice trades
  recall/speed/memory explicitly
  -> https://github.com/facebookresearch/faiss +
     https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
  -> verified (existence, entailment; official repo + wiki)
- **C10.** sqlite-vec adds vector KNN to SQLite as a zero-dependency
  extension; stable releases use brute-force (exact) search - disk-backed,
  simple, impractical above ~100k vectors
  -> https://github.com/photostructure/node-vector-bench +
     https://d-central.tech/self-hosted-vector-databases/
  -> verified existence; entailment [secondary] (benchmark harness +
  community comparison; scale ceiling is one benchmark's finding)
- **C11.** LanceDB is an embedded Apache-2.0 vector store (Lance columnar
  format) with vector search, full-text search, and SQL in one local table -
  no server
  -> https://github.com/lancedb/lancedb
  -> verified (existence, entailment; official repo README)
- **C12.** Server-tier open-source options exist (Qdrant Apache-2.0, Weaviate
  BSD-3, Milvus, pgvector for Postgres); Elasticsearch downloadable builds are
  Elastic License/SSPL - not OSI-open; OpenSearch is the Apache-2.0 drop-in
  -> https://d-central.tech/self-hosted-vector-databases/
  -> verified existence; entailment [secondary] - license column needs
  re-verification before encoding in skill text

### Hybrid retrieval + reranking

- **C13.** Reciprocal Rank Fusion (`score = Σ 1/(k+rank)`, k≈60 near-optimal,
  choice not critical) combines rankings unsupervised without score
  calibration and outperformed individual systems and Condorcet Fuse in TREC
  experiments
  -> https://cormack.uwaterloo.ca/cormacksigir09-rrf
  -> verified (existence, entailment; SIGIR 2009 original paper page)
- **C14.** Lexical (BM25) and dense retrievers are complementary - hybrid
  fusion improves relevance; convex score combination can outperform RRF and
  RRF is parameter-sensitive, so the fusion method is corpus-dependent
  -> https://dl.acm.org/doi/10.1145/3596512 +
     https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid
  -> verified (existence, [abs] entailment for TOIS analysis; Elastic post is
  [vendor] but consistent with the literature)
- **C15.** Cross-encoder rerankers score query+document jointly (more
  accurate than bi-encoder, too slow for full corpus); standard pattern:
  bi-encoder/lexical retrieves top-50–100, cross-encoder reranks to final
  top-k; open models exist (bge-reranker base/large, jina-reranker)
  -> https://bge-model.com/bge/bge_reranker.html +
     https://bge-model.com/Introduction/reranker.html
  -> verified (existence, entailment; BGE official docs)
- **C16.** Contextual Retrieval (prepending chunk-specific context before
  embedding and before BM25 indexing) reduced top-20 retrieval failure rate
  35% (embeddings alone), 49% (+BM25), 67% (+reranking) on Anthropic's eval
  -> https://www.anthropic.com/engineering/contextual-retrieval
  -> verified existence; entailment [vendor] - numbers are Anthropic's own
  eval; reproduction cookbook exists at
  github.com/anthropics/claude-cookbooks (verified existence)

### Evaluation

- **C17.** RAGAS provides reference-free RAG metrics - faithfulness, answer
  relevance, context precision/recall - usable without ground-truth human
  annotations; EACL 2024 demo paper
  -> https://arxiv.org/abs/2309.15217 +
     https://aclanthology.org/2024.eacl-demo.16.pdf
  -> verified (existence, entailment)
- **C18.** Deterministic retrieval metrics (hit rate, recall@k, MRR, Pass@k
  against golden-chunk labels) are standard practice - Chroma's report and
  Anthropic's cookbook both evaluate retrieval with labeled golden chunks
  -> https://www.trychroma.com/research/evaluating-chunking +
     https://github.com/anthropics/claude-cookbooks/blob/main/capabilities/contextual-embeddings/guide.ipynb
  -> verified (existence, entailment)
- **C19.** LLM-as-judge struggles precisely on questions the judge cannot
  itself answer; supplying a human-written reference answer improves
  judge–human agreement (weaker judge + good reference beats stronger judge +
  synthetic reference)
  -> https://arxiv.org/abs/2503.05061
  -> verified (existence, [abs] entailment)
- **C20.** When the judge is no more accurate than the evaluated system, no
  debiasing method can cut required ground-truth labels by more than half;
  self-preference bias exists in model-as-judge
  -> https://arxiv.org/abs/2410.13341
  -> verified (existence, [abs] entailment)
- **C21.** Large-scale judge study (21 judges, ~541k judgments) found
  universal kappa deflation vs exact-match agreement (33–41pp), position bias
  in production judges, and rank instability across benchmarks
  -> https://arxiv.org/abs/2606.19544
  -> verified (existence, [abs] entailment)

### Agentic / tool-loop retrieval

- **C22.** Agentic RAG = the LLM treats retrieval as a tool inside a
  reasoning loop (planning, reflection, tool use, iterative query refinement);
  taxonomy by agent cardinality/control/autonomy
  -> https://arxiv.org/abs/2501.09136
  -> verified (existence, entailment; survey)
- **C23.** Autonomous retrieval loops carry systemic risks: compounding
  hallucination propagation, memory poisoning, retrieval misalignment,
  cascading tool-execution failures - and static evaluation does not capture
  them
  -> https://arxiv.org/pdf/2603.07379
  -> verified (existence, [abs] entailment; SoK paper)
- **C24.** In a 450-fold corpus-scaling study, agentic file-system
  exploration led at smallest tiers but cost 39x query tokens; BM25 overtook
  it around ~10M corpus tokens and led at every larger tier (margin ~20pt at
  full scale); agentic reasoning worked best *after* ranked discovery, not in
  place of it
  -> https://arxiv.org/html/2607.26497v2
  -> verified (existence, entailment - full-text HTML read of abstract+setup)
- **C25.** A well-tuned BM25 retriever in an agentic loop (Pi-Serini +
  frontier LLM) reached 83.1% accuracy on BrowseComp-Plus, outperforming
  released dense-retriever agents; BM25 tuning alone +18pt accuracy, deeper
  retrieval +25.3pt evidence recall
  -> https://www.alphaxiv.org/abs/2605.10848
  -> verified (existence, [abs] entailment; alphaXiv summary of arXiv paper)
- **C26.** For repository-level code completion, index-free ripgrep-based
  lexical retrieval matched sophisticated graph-based RAG baselines; adding
  identifier-weighted reranking + structure-aware dedup (GrepRAG) outperformed
  SOTA on CrossCodeEval/RepoEval
  -> https://dl.acm.org/doi/abs/10.1145/3832136
  -> verified (existence, [abs] entailment; PACMSE paper)
- **C27.** Retrieval must cross a precision threshold before it helps a
  coding agent: BM25 at 0.375 precision degraded the agent; only the
  0.677-precision retriever bought efficiency (+1.2pp resolve, −15% rounds)
  -> https://arxiv.org/pdf/2608.05886
  -> verified (existence, [abs] entailment; CodeGrep paper)
- **C28.** Anthropic's Claude Code uses ripgrep-based agentic search over the
  live tree instead of a vector index (early versions used RAG + local vector
  DB; switched after internal benchmarks); corroborated by multiple
  independent write-ups and the shipped explore-agent prompt
  -> https://rust-trends.com/posts/ripgrep-claude-code/ +
     https://neurals.ca/tech/claude/agentic-search/
  -> verified existence; entailment [secondary] - consistent reports +
  observable tool design; original claim attributed to Anthropic podcast
- **C29.** Excessive retrieval harms agentic tasks
  -> source `skills/memory-management/SKILL.md:84` (arXiv:2608.15008)
  -> verified as internal citation; paper not fetched - flag for full
  verification before the skill cites it

### Long context vs RAG; failure modes

- **C30.** When resourced sufficiently, long-context LLMs outperform RAG on
  average, but RAG is dramatically cheaper; a self-routing hybrid preserves
  LC-level quality at much lower cost (SELF-ROUTE, Google, EMNLP 2024
  Industry)
  -> https://aclanthology.org/anthology-files/pdf/emnlp/2024.emnlp-industry.66.pdf
  -> verified (existence, entailment; arXiv:2407.16833)
- **C31.** Answer quality vs number of retrieved chunks is an inverted U -
  there is a sweet spot; more retrieved context eventually hurts (OP-RAG)
  -> https://arxiv.org/html/2409.01666
  -> verified (existence, [abs] entailment)
- **C32.** In long-context RAG, only a handful of recent SOTA LLMs maintain
  consistent accuracy above ~64k tokens of retrieved context
  -> https://arxiv.org/pdf/2411.03538
  -> verified (existence, [abs] entailment)
- **C33.** Relevant information placed mid-context is used worse than at the
  beginning/end (U-shaped position effect; mid-context can drop below
  closed-book)
  -> https://arxiv.org/abs/2307.03172
  -> verified (existence, entailment; TACL 2024 version)
- **C34.** Seven canonical RAG failure points from 3 case studies (missing
  content; missed top-ranked docs; not consolidated in context; not
  extracted; wrong format; incorrect specificity; incomplete answers);
  RAG validation is only feasible during operation; robustness evolves
  rather than being designed in upfront
  -> https://arxiv.org/abs/2401.05856
  -> verified (existence, entailment; CAIN 2024, IEEE 10556182)
- **C35.** HyDE improves zero-shot dense retrieval without relevance labels:
  LLM generates a hypothetical answer document, encoder embeds it, real
  documents are retrieved by similarity to the hypothetical vector
  -> https://arxiv.org/abs/2212.10496
  -> verified (existence, entailment)
- **C36.** Zero-dependency BM25 is reachable from Python's stdlib: SQLite
  FTS5 ships a built-in `bm25()` rank function plus `snippet()`/`highlight()`;
  pip alternatives exist (`rank_bm25` Apache-2.0 Okapi/BM25L/BM25+; `bm25s`
  fast scipy-sparse implementation, order-of-magnitude QPS over rank_bm25 in
  its reported BEIR benchmarks)
  -> https://www.sqlite.org/fts5.html +
     https://pypi.org/project/rank-bm25/ +
     https://github.com/xhluca/bm25s
  -> verified (existence, entailment for SQLite/PyPI; bm25s speed claim is
  [vendor-of-the-lib] README numbers)

## Synthesis by coverage area

1. **Chunking.** Structure-aware + recursive splitting is the defensible
   default (C2, C3); no universal winner (C1). Chunk boundaries are the
   highest-leverage knob - fix splitting before swapping embedding models
   (C3, weakly C4). For Markdown docs: header-based split then recursive
   size cap (LangChain docs pattern, C2). For code: per-language separators
   exist (C2); identifier-aware handling matters (C26). Semantic/LLM
   chunkers are competitive but cost-adding options, not defaults (C3, C5).
   Context-poor fragments lose retrieval quality - a "contextual prefix"
   step is the biggest verified single gain but is vendor-evaluated (C16).

2. **Embeddings.** Pick from MTEB-filtered candidates by domain (code
   retrieval tasks exist there), not by hype (C6). Local models are
   real: fastembed/ONNX and sentence-transformers run offline after a
   one-time download (C7, C8). Hosted embeddings are a latency/quality
   trade, not a capability requirement - escalate only on measured local
   failure (tier model below).

3. **Vector stores.** In-process is the default for project-scale corpora:
   FAISS (index algebra, max control) (C9), sqlite-vec (exact KNN inside the
   DB the corpus may already live in; brute-force scale ceiling ~100k) (C10),
   LanceDB (embedded, vectors+FTS+SQL in one store) (C11). Server DBs are a
   deployment tier, not a quality tier (C12).

4. **Hybrid + reranking.** Lexical misses paraphrase; dense misses exact
   identifiers - they are complementary, fuse them (C14). RRF (k=60) is the
   zero-config fusion baseline (C13); note convex-combination can beat it, so
   measure on the corpus (C14). Cross-encoder rerank on top-50–100 candidates
   is the standard accuracy step; open rerankers exist for local use (C15).
   Contextual chunk prefixes help both embedding and BM25 legs (C16
   [vendor]).

5. **Evaluation.** Two layers: (a) deterministic retrieval eval - build a
   golden set of query→expected-passage pairs, measure hit rate/recall@k/MRR
   (C18); (b) LLM-graded answer metrics - faithfulness, answer relevance,
   context precision/recall via RAGAS-style frameworks (C17). LLM judges need
   human reference answers and calibration; ungrounded judging is unreliable
   (C19, C20, C21). Practical loop for a skill: golden retrieval eval first,
   LLM eval second, human spot-check on judge–data disagreement.

6. **Agentic / tool-loop retrieval.** Retrieval-as-tool in the agent loop is
   the current paradigm (C22). Evidence consistently favors starting simple:
   agent+grep matches or beats fancier stacks at small scale (C24, C26, C28);
   BM25 index overtakes ad-hoc exploration at ~10M corpus tokens (C24); tuned
   BM25 in an agentic loop beats released dense-retriever agents on a deep-
   research benchmark (C25). Quality gate: below a precision threshold,
   retrieval *hurts* the agent (C27); too much retrieved context hurts too
   (C29, C31). Agentic loops need risk awareness - error compounding, memory
   poisoning (C23).

7. **Failure modes.** Barnett's seven FPs give the checklist backbone (C34).
   Plus: inverted-U in retrieved-chunk count (C31), >64k-token accuracy decay
   in most models (C32), lost-in-the-middle ordering effects - put the best
   chunks at the edges (C33), stale/duplicated index drift (C34 FP3-family +
   knowledge-modeling's incremental-merge discipline), judge bias in eval
   (C19–C21), retrieval below precision threshold actively degrading the
   agent (C27).

8. **Teach vs omit (for the skill).**
   Teach: the tier ladder with explicit escalation evidence; golden-set
   retrieval eval before any embedding work; chunking discipline (structure-
   aware default, measure sizes); hybrid + rerank recipe at tier 2;
   provenance (every retrieved chunk cites `path:line`, matching
   `knowledge-modeling`'s extracted-fact convention); staleness/dedup
   handling; failure-mode checklist; agentic pattern = retrieve-as-tool after
   ranked discovery, bounded loops (context-hygiene cost guards apply).
   Omit: vendor walkthroughs and hosted-service setup (provider-neutral
   boundary); a named "best" embedding model (point at MTEB - leaderboard
   churns); shipped runtime/index over the bundle (vision boundary);
   GraphRAG and retriever fine-tuning (construction walls C24, skill scope);
   MCP proposals (contract boundary); implementation code (contract).

## Recommended tier model

Escalate only when the current tier's *measured* failures justify it
(golden-set recall/hit-rate misses, not vibes). Every tier cites ≥1 verified
claim.

| Tier | Retrieval | Deps | When sufficient | Evidence |
|---|---|---|---|---|
| **0 — Agentic lexical** | glob/grep(ripgrep)/read loops over the live tree | none | small corpora, code-shaped queries, fresh-tree correctness needed | C24 (FS-agent leads small tiers), C26 (grep ≈ graph RAG for code), C28 (Claude Code), C18 |
| **1 — Lexical index** | BM25 via SQLite FTS5 `bm25()` (stdlib) or `rank_bm25`/`bm25s` | stdlib or one pip pkg | >~10M corpus tokens, repeated queries, identifiers/exact terms | C24 (BM25 wins at scale), C36 (FTS5/pkgs), C25 (tuned BM25 strong in agentic loop) |
| **2 — Local hybrid** | local embeddings (fastembed / sentence-transformers) + in-process store (sqlite-vec / FAISS / LanceDB), RRF-fused with BM25, optional local cross-encoder reranker (bge-reranker) | opt-in `requirements.txt` | paraphrase/synonym recall needed; multilingual; lexical eval misses | C6 (MTEB pick), C7–C8 (local models), C9–C11 (stores), C13–C15 (fusion+rerank), C16 (contextual prefixes [vendor]) |
| **3 — Hosted / server** | hosted embeddings or server vector DB (Qdrant/Weaviate/Milvus/pgvector) | consent + credentials; never default | corpus exceeds local scale, managed ops required, team infra already exists | C12 (options), C30 (cost framing — RAG chosen for cost, escalate deliberately) |

Escalation triggers (skill should teach): golden-set recall@k below target;
paraphrase-heavy queries failing lexical (tier 1→2); corpus/ops scale beyond
local (tier 2→3); per-query latency budget forcing approximate indexes.

De-escalation guard: before each tier-up, re-run the golden eval on the
current tier - C24/C25 show lexical tiers are stronger than assumed.

## Self-quiz

1. **Which decision does each verified claim support?** C2/C3/C5 → chunking
   defaults; C6–C8 → embedding tier-2 model selection process; C9–C12 →
   store tiering; C13–C16 → hybrid+rerank recipe; C17–C21 → eval
   architecture; C22–C29 → agentic pattern and its bounds; C30–C33 →
   context-budget limits; C34–C36 → failure checklist + zero-dep baseline.
   C24/C26/C28 jointly justify tier 0; C36+C24 justify tier 1.
2. **Which decision lacks a verified claim?** (a) Exact numeric thresholds
   for tier escalation (corpus size, recall@k cutoff) - must be taught as
   "measure on your corpus", not fixed numbers. (b) Whether SQLite FTS5 is
   compiled into every target Python install - platform-dependent; skill must
   include a feature-check step. (c) Best chunk sizes for *code* vs *prose*
   under local small embeddings - covered only directionally (C2–C4). (d)
   C29's underlying paper not fetched.
3. **Which claims rest on a single source?** C4 (single blog/corpus -
   flagged weak), C10 scale ceiling, C12 license column, C14 Elastic post
   (corroborated by C13), C16 (vendor eval - cookbook reproduction exists),
   C21, C23, C25, C27, C31, C32 (single papers), C28 (multiple secondary
   write-ups + observable tool design).
4. **What would change the recommendation?** A replicated public benchmark
   showing dense-first retrieval beating tuned BM25 on code corpora at
   project scale would collapse tiers 0–1; a verified failure of FTS5
   availability on stock Python would swap tier-1's default implementation;
   new eval evidence that local cross-encoders underperform at 384-dim scale
   would soften the reranker step.

## Residual gaps

- No direct corpus-size→tier threshold constants verified (C24's ~10M-token
  crossover is one study on one enterprise benchmark - directionally useful,
  not a constant).
- Code-specific chunking evaluation is thinner than prose chunking (GrepRAG
  bypasses chunking entirely by design).
- sqlite-vec IVF/DiskANN paths are alpha-stage per secondary source (C10) -
  re-check at skill-writing time.
- LLM-as-judge bias literature is large; C19–C21 cover the load-bearing
  points, not the full taxonomy.
- Frozen-input hashes in the contract were not independently re-verified
  here (read-only lane, no exec tool); orchestrator's verify step covers.
