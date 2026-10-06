# ADR 004 - `rag` skill: provider-neutral offline-first tier model

- Status: proposed (pending G3 construction)
- Date: 2026-10-05
- Track: agent-docs-rag
- Evidence base: `.devin/research/rag-practices.md` (36 verified claims)

## Context

The bundle needs a skill that teaches agents to build retrieval over
arbitrary project corpora. Bundle culture is stdlib-first, offline-first,
consent-gated deps (ARCHITECTURE_MANIFEST §3; vision NFR-1/NFR-2). Research
shows retrieval quality is corpus- and scale-dependent, and that simple
lexical/agentic retrieval is stronger than assumed for code corpora.

## Decision

The skill teaches a 4-rung ladder, escalated only by measured failure:

| Tier | Retrieval | Deps |
|---|---|---|
| 0 — Agentic lexical | glob/grep/read loops over live tree | none |
| 1 — Lexical index | BM25 (SQLite FTS5 `bm25()` or `rank_bm25`/`bm25s`) | stdlib / one pip pkg |
| 2 — Local hybrid | local embeddings + in-process store + RRF fusion + optional reranker | opt-in requirements.txt |
| 3 — Hosted/server | hosted embeddings or server vector DB | consent + credentials; never default |

Skill content rules: golden-set retrieval eval before any embedding work;
structure-aware chunking default; provenance (`path:line`) on every chunk;
failure-mode checklist; escalation triggers are measured, not fixed
constants. Omits: vendor defaults, named "best" models (points at MTEB),
shipped runtime, MCP, implementation code.

## Alternatives rejected

- 3-rung model without tier 0: contradicted by C24/C26/C28 (grep/agentic
  retrieval matches or beats indexed stacks at project scale).
- Embeddings-first teaching: contradicted by C3/C4 (chunking > model) and
  C25/C27 (tuned BM25 strong; weak retrieval harms agents).
- Vendor-anchored quickstart: violates provider-neutral boundary (vision).

## Consequences

- New skill `skills/rag/` + `reference/` files; manifest + SKILL-TIERS
  wiring required (audit keeps 67-name sync invariant).
- Deps, if any, live only under opt-in paths; no hook/script changes.
- Frozen-input drift on `.devin/research/rag-practices.md` invalidates the
  skill's claim citations - re-verify C29/license column at write time.
