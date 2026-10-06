# Review: skills/rag/ (contract 07)

**VERDICT: FIX: [S1]** - one uncited numeric threshold; all other checks green.

Scope: `skills/rag/SKILL.md` (5,691 B), `reference/tier-recipes.md` (5,399 B),
`reference/eval-and-failures.md` (3,696 B). Frozen-input hashes re-verified:
rag-practices.md = 04960e75... and SKILL.md = d6a765bb... (match contract-07).

## Standards axis: PASS

Criteria from `skills/writing-skills/SKILL.md` + `reference/writing-for-agents.md`.

- Frontmatter: `name: rag` == dir; description is discovery-form ("Use
  when...") listing four distinct branches; `triggers: [user, model]`
  present; description ~300 chars < 1024.
- Budget: 5,691 bytes <= 10KB (contract-05 VF2).
- Progressive disclosure: pointers at SKILL.md:34 (`reference/tier-recipes.md`),
  SKILL.md:62 and :66 (`reference/eval-and-failures.md`) all resolve; pointer
  text carries branch conditions, not content.
- Telegraphic: table + tight bullets; no prose padding.
- Vendor neutrality: no vendor/model named as default; teach/omit list
  (SKILL.md:99-103) encodes it. Named stores/models appear only as options
  or evidence sources (C16 Anthropic named as the eval's source, not a
  default - compliant).
- Em-dash: zero non-ASCII chars in all three files (byte-scan).
- AI signature: none (grep + validator patterns clean).
- `python scripts/validate-skill-format.py skills` -> `rag` PASS, score 100;
  68/68 skills passing.
- writing-for-agents specifics: negations used only as hard guardrails paired
  with positive targets ("never by hype" -> MTEB pointer, SKILL.md:59-60);
  leading word "tier" carries the ladder consistently.

Smells (non-blocking):

- SKILL.md:70-77 vs eval-and-failures.md:52-67 - failure checklist appears in
  both files, but SKILL.md holds the judgment lines and the reference holds
  the full mapped table; deliberate branch-splitting, not drift.

## Spec axis: FIX (1 Important, 1 Minor)

Contract-05 content requirements: ALL PRESENT.
frontmatter branches (SKILL.md:3-4); tier ladder 0-3 with measured
escalation (:15-24); golden-set eval before embedding work (:38-42);
structure-aware chunking default (:43-50); provenance `path:line` (:51-54);
failure-mode checklist (:64-84); teach/omit boundary (:93-103);
`reference/tier-recipes.md` zero-dep FTS5 shape (:34-40); eval sketch with
hit rate/recall@k/MRR (eval-and-failures:22-28); failure catalog mapped to
C-numbers (:52-67).

Claim traceability: 30+ C-citations sample-audited against
rag-practices.md claim map (C24, C26, C28, C25, C18, C27, C2, C3, C4, C1,
C5, C6, C36, C7, C8, C9, C10, C11, C13, C14, C15, C16, C12, C30, C31, C33,
C32, C23, C22, C34, C17, C19, C20, C21). All cited numbers exist; all say
the claimed thing; flag markers carried ([abs]/[vendor]/[secondary]/
[single-corpus]/[vendor-of-the-lib]). C29 correctly absent (contract-05
forbade it). C12 license column referenced only via its unverified flag
(tier-recipes:99-100) - correct handling.

Findings:

- **S1 (Important)** `skills/rag/reference/eval-and-failures.md:11` - "30+
  pairs minimum" is a fixed numeric threshold with no C-number; no
  golden-set size floor exists in rag-practices.md, and self-quiz 2a
  (rag-practices.md:407-409) directs that exact numeric thresholds be
  taught as "measure on your corpus", not fixed numbers. Violates
  contract-05 traceability clause ("every practice you state must trace
  to a C-number"). Fix: drop the number or mark it as heuristic.
- **S2 (Minor)** `skills/rag/SKILL.md:57` - "(C36)" appended to the
  FTS5-compiled feature-check; C36 covers `bm25()`/`snippet()`/`highlight()`
  existence, while platform-dependence is stated only in research
  self-quiz 2b (rag-practices.md:409-411), which carries no C-number.
  The practice itself is correct and research-mandated; the same
  statement in tier-recipes.md:37-40 is correctly left uncited.

## Trigger-collision boundaries

- research: invoke **rag** when designing/building/evaluating a retrieval
  system over a corpus (chunking, index, golden-set eval); invoke
  **research** when answering one specific question now via primary
  sources or multi-pass codebase search - research performs the search,
  rag builds the repeatable capability. (Sharpest collision: rag's "agent
  can't find things in docs" overlaps research's "exploration beyond a
  quick grep".)
- knowledge-modeling: invoke **rag** when retrieving relevant
  passages/chunks from a corpus; invoke **knowledge-modeling** when
  extracting typed entities/relations with provenance into a versioned
  knowledge graph or validating tool output against an ontology.
- memory-management: invoke **rag** for within-corpus passage retrieval
  during a task; invoke **memory-management** for what persists across
  sessions (MEMORY.md, `.devin/memory/`, auto-memory hygiene).
- context7: invoke **rag** for retrieval over the project's own corpus;
  invoke **context7** when fetching current third-party library docs via
  the Context7 API.

## Evidence (commands run)

- python byte-scan: 0 non-ASCII chars in the three files (no em-dash,
  no smart quotes).
- `grep -rniE "pinecone|weaviate|openai|cohere|qdrant cloud|generated
  with|co-authored" skills/rag/` -> no matches.
- `python scripts/validate-skill-format.py skills` -> rag PASS (100).
- Sizes (Get-Item): 5,691 / 5,399 / 3,696 bytes.
- sha256 of both frozen inputs match contract-07.
