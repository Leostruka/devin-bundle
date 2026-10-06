# RAG tier recipes

Per-tier build recipes for the ladder in `../SKILL.md`. C-numbers cite
`.devin/research/rag-practices.md`; flag markers (`[abs]`, `[vendor]`,
`[secondary]`, `[single-corpus]`) carry over from the claim map - treat
flagged claims as directional, not law.

## Tier 0 - Agentic lexical

No index. The agent runs glob/grep/read loops over the live tree.

- Search for identifiers and distinctive literals first, then structural
  terms (file names, headings, config keys).
- Bound the loop: fixed max searches per question; stop when a cited
  `path:line` answer exists.
- Fresh-tree correctness for free: nothing to keep in sync.

Evidence: filesystem exploration leads at small corpus scale but costs
~39x query tokens vs indexed retrieval in one corpus-scaling study
(C24); index-free lexical retrieval matches graph-based RAG baselines
for repository-level code completion, and identifier-weighted reranking
plus structure-aware dedup beats them (GrepRAG, C26); a shipped coding
agent runs ripgrep over the live tree instead of a vector index
(C28 [secondary]).

Sufficient while: corpus small enough that searches stay cheap, queries
are code-shaped, and the golden set passes.

## Tier 1 - Lexical index (BM25)

Chunk the corpus (structure-aware split + recursive size cap, C2), then
index chunks in a BM25 store.

- **Zero-dependency shape:** SQLite FTS5. One table per chunk carrying
  `doc_path`, `start_line`, `end_line`, `text`; a FTS5 virtual table
  over `text` gives `bm25()` ranking plus `snippet()`/`highlight()`
  for result display (C36). Feature-check first: FTS5 presence in the
  target Python's sqlite3 is platform-dependent - probe with a
  `CREATE VIRTUAL TABLE ... USING fts5` smoke test before committing
  to this path.
- **Pip alternatives:** `rank_bm25` (Okapi/BM25L/BM25+ variants) or
  `bm25s` (fast sparse implementation; its reported BEIR numbers show
  order-of-magnitude QPS gains, [vendor-of-the-lib] README) (C36).
- Tokenizer matters for code: split identifiers on case/underscore
  boundaries so `parse_config` matches `parseConfig` call sites
  (identifier-aware handling is what made GrepRAG win, C26).
- Keep the index rebuildable: store `path:line` provenance and a content
  hash per chunk; rebuild or incremental-merge on drift.

Evidence: BM25 overtakes agentic exploration around ~10M corpus tokens
in the scaling study and leads at every larger tier (C24, one study -
directional, not a fixed constant); tuned BM25 in an agentic loop beat
released dense-retriever agents on a deep-research benchmark (C25 [abs]).

Escalate when: golden-set recall@k misses concentrate on paraphrase /
synonym queries that BM25 cannot bridge.

## Tier 2 - Local hybrid

Add dense retrieval alongside BM25, fuse, rerank. All local - no API
keys (C7).

- **Embeddings:** choose candidates from MTEB filtered to the corpus
  domain (code/legal/multilingual retrieval tasks exist; C6). Local
  libraries: sentence-transformers (`all-*` models trade quality vs
  speed) and fastembed (ONNX, downloads once, caches, runs offline);
  BGE-family models are common local defaults with quantized variants
  (C7, C8). Name no model as "the" default in committed artifacts -
  leaderboards churn; point at MTEB.
- **Stores:** in-process only. FAISS gives explicit index-algebra
  control (Flat/IVF/PQ/HNSW - recall vs speed vs memory, C9);
  sqlite-vec adds brute-force KNN inside the SQLite file the chunks may
  already live in (practical ceiling ~100k vectors per a secondary
  benchmark, C10); LanceDB packs vectors + FTS + SQL in one embedded
  table (C11).
- **Fusion:** Reciprocal Rank Fusion, `score = sum(1/(k+rank))` with
  k~60, is the zero-config baseline and beat individual systems in TREC
  (C13). Lexical + dense are complementary - fusion improves relevance,
  but convex score combination can beat RRF, so measure on your corpus
  (C14 [abs]).
- **Rerank:** retrieve top-50 to top-100 candidates bi-encoder/lexical,
  rerank to final top-k with a local cross-encoder (open rerankers
  exist, e.g. bge-reranker family, jina-reranker; C15).
- **Contextual prefixes (optional):** prepend a short chunk-specific
  context line before embedding and before BM25 indexing. Vendor eval
  reports large failure-rate reductions (35%/49%/67% by configuration),
  but the numbers are the vendor's own - reproduce on your golden set
  before adopting (C16 [vendor]).
- Deps live under an opt-in requirements file only.

Escalate when: corpus or ops scale beyond local capacity, or the
latency budget forces approximate/server indexes.

## Tier 3 - Hosted / server

Consent + credentials required; never the default. Open-source server
vector DBs exist (Qdrant, Milvus, pgvector-for-Postgres among them);
hosted embedding APIs are a latency/quality/ops trade, not a capability
requirement (C12; license specifics re-verify at adoption - the
research's license column is flagged unverified). Long-context
comparison frames the choice as cost, not quality: RAG stays
dramatically cheaper; a self-routing hybrid preserves most long-context
quality at lower cost (C30).

## De-escalation guard

Before each tier-up, re-run the golden eval on the current tier (C24,
C25). If lexical passes, stay. Downgrade freely when an upper tier stops
earning its deps.
