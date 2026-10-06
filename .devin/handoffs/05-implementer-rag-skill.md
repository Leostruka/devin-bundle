# Delegation contract

## Contract

- **Contract ID**: 05-implementer-rag-skill
- **Objective**: Create `skills/rag/` - a skill teaching agents to design,
  build, and evaluate RAG over arbitrary project corpora, encoding the
  4-tier model and rules in `.devin/research/rag-practices.md` and ADR-004.
- **Profile**: implementer
- **Lane**: direct on main worktree (`skills/rag/` is new - exclusive)
  - **Lane setup**: none
  - **Lane teardown**: none
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\.devin\research\rag-practices.md`
    (the ONLY source of factual RAG claims - every practice you state must
    trace to a C-number there)
  - `D:\Programing\ai_workspace\devin-bundle\.devin\adr\004-rag-skill-tier-model.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\writing-skills\SKILL.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\writing-skills\reference\writing-for-agents.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\knowledge-modeling\SKILL.md`
    (house-style reference: terse, modes/reference split, provenance norm)
- **Readable refs**: `.devin/vision.md`, `.devin/ARCHITECTURE_MANIFEST.md`,
  `data/bundle-models.json` (if you mention model routing)
- **Frozen inputs** (re-hashed at verify; drift fails the contract):
  - `.devin/research/rag-practices.md` sha256:c3f894d1fffb8f36e76914b6aeaf1921bc6e481a01676ec8f77ddfd3dc6e1a33
  - `skills/writing-skills/SKILL.md` sha256:9909a07a8301c8e2ff1a6a4256a8b44398273fbcfe964c14335450b4ea89f109
  - `skills/writing-skills/reference/writing-for-agents.md` sha256:26918be17e60c8ac5e32350f2bd45c45dd2d2d63476bba68c79f21525e34a890
- **Output**: `skills/rag/SKILL.md` + `skills/rag/reference/*.md` (1-3
  files) + handoff doc at `.devin/handoffs/05-implementer-rag-skill-out.md`
- **Tools allowed**: profile default
- **Peer consults**: none
- **Boundaries (do NOT)**:
  - touch `manifest.json`, `.devin/docs/SKILL-TIERS.md`, or any existing
    file - wiring is a later contract
  - name a vendor/hosted service or embedding model as "the default"
    (provider-neutral; point at MTEB for model choice)
  - ship runnable code, a vector index, MCP config, or requirements.txt
    entries - the skill is guidance, not a runtime
  - cite arXiv:2608.15008 (C29) or the server-DB license column - both are
    flagged unverified in the research's open items; use only verified claims
  - write above ~10KB in SKILL.md (push detail to `reference/`)
  - use em-dash (U+2014) anywhere - project gate blocks it
  - include AI signatures, or narrate "how we built this"
- **Content requirements**:
  - frontmatter: `name: rag`, `description` written as discovery triggers
    ("Use when...") covering: retrieval over a corpus, chunking/embeddings/
    vector store questions, RAG evaluation, "my agent can't find things in
    docs"; add `triggers: [user, model]`
  - body: the tier ladder (0 agentic-lexical, 1 BM25 index, 2 local hybrid,
    3 hosted/server) with measured-escalation triggers; golden-set retrieval
    eval BEFORE any embedding work; structure-aware chunking default;
    provenance convention (chunk cites path:line); failure-mode checklist;
    clear teach/omit boundary
  - `reference/`: tier recipes (incl. zero-dep BM25 via SQLite FTS5 shape),
    eval-harness sketch (golden query->passage set, hit rate/recall@k/MRR),
    failure catalog mapped to research C-numbers
- **Termination**: max 80 turns / 60 minutes; stop when SKILL.md + reference
  files pass VFs
- **Verification (VFs)**:
  - VF1: `python scripts/validate-skill-format.py skills/rag/SKILL.md`
    (or the script's actual CLI) -> pass
  - VF2: SKILL.md size <= 10KB (`bytes`); dir name == frontmatter name
  - VF3: tier table/list with tiers 0-3 present; golden-set-eval-before-
    embeddings rule present; no vendor-as-default strings
    (grep -iE "pinecone|weaviate cloud|openai embedding|cohere" -> none in
    normative position)
  - VF4: every factual practice statement maps to a research claim (spot
    audit: pick 5 claims in SKILL.md/reference, each cites or paraphrases a
    C-number that exists in rag-practices.md)
  - VF5: `python audit.py` -> 0 errors

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
