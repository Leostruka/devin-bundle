# Delegation contract

## Contract

- **Contract ID**: 01-researcher-rag-practices
- **Objective**: Produce `.devin/research/rag-practices.md`, the verified
  research base for a new `rag` skill that teaches agents to design, build,
  and evaluate retrieval-augmented generation in arbitrary projects.
  Provider-neutral, offline-first tier model: lexical baseline (zero deps)
  -> local embeddings -> hosted vector DB.
- **Profile**: researcher
- **Lane**: read-only
  - **Lane setup**: none
  - **Lane teardown**: none
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\.devin\vision.md`
  - `D:\Programing\ai_workspace\devin-bundle\.devin\plans\2026-08-29-hyper-extract.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\knowledge-modeling\SKILL.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\memory-management\SKILL.md`
  - `D:\Programing\ai_workspace\devin-bundle\skills\writing-skills\SKILL.md`
- **Readable refs**: `.devin/CONTEXT.md`, `.devin/ARCHITECTURE_MANIFEST.md`,
  `.devin/development-case.md`, `skills/context-hygiene/SKILL.md`
- **Frozen inputs** (re-hashed at verify; drift fails the contract):
  - `.devin/vision.md` sha256:ee8e681d15264ae4c6b8b2fac73a4bdc79eb8cc3fa54386ac48258baea332479
  - `.devin/plans/2026-08-29-hyper-extract.md` sha256:394f6a8104cd8792c5cb7444797d4fc29c862bb4e426142abb5b308931c932f8
  - `skills/knowledge-modeling/SKILL.md` sha256:85e9587bde6a0d17ee1d92ac64f857eb1109bb6ec43f2a169baa08123cbc101d
  - `skills/writing-skills/SKILL.md` sha256:9909a07a8301c8e2ff1a6a4256a8b44398273fbcfe964c14335450b4ea89f109
  - `skills/memory-management/SKILL.md` sha256:c5686b5262e90df001a5fd846ff00684d76ba82a56ef99a9d8cdc92dff2e0d60
- **Output**: report at `.devin/research/rag-practices.md` + handoff doc at
  `.devin/handoffs/01-researcher-rag-practices-out.md` (template:
  `skills/project-orchestrator/templates/handoff-doc.md`)
- **Tools allowed**: profile default (read, grep, glob, web_search, webfetch)
- **Peer consults**: none
- **Boundaries (do NOT)**:
  - write outside `.devin/research/rag-practices.md` and the handoff path
  - modify any existing file (skills, manifest, docs, plans)
  - propose a stack default without a claim->source line
  - recommend a specific vendor/hosted service as the default tier
  - exceed scope: no implementation code, no skill text, no MCP proposal
- **Termination**: max 60 turns / 60 minutes; stop when the coverage
  self-quiz is answered with real residual gaps
- **Verification (VFs)**:
  - VF1: file `.devin/research/rag-practices.md` exists and is non-empty
  - VF2: file contains `## Criteria`, `## Queries`, `## Coverage` sections
    (PRISMA-lite header per research-protocol)
  - VF3: every load-bearing claim appears in a claim->source mapping
    (grep for `-> http` or `-> source` produces >=10 lines)
  - VF4: file contains a self-quiz answering the 4 protocol questions
  - VF5: recommended tier model is stated and every tier cites >=1 verified
    claim
- **Coverage required**: chunking strategies; embedding choices (open/local
  vs hosted); vector stores (in-process vs server); hybrid retrieval +
  reranking; RAG evaluation methods; agentic/tool-loop retrieval patterns;
  known failure modes; what a coding-agent skill should teach vs omit.

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
