# Handoff: 05-implementer-rag-skill

## Result

- **Status:** DONE_WITH_CONCERNS (deliverables complete; VF5 red on wiring
  counts the contract forbids me to touch)

## Files written

- `skills/rag/SKILL.md` (5,691 bytes)
- `skills/rag/reference/tier-recipes.md`
- `skills/rag/reference/eval-and-failures.md`

No existing files modified.

## VF results (run locally)

| VF | Result | Evidence |
|---|---|---|
| VF1 `python scripts/validate-skill-format.py skills/` | PASS | 68 skills, 68 passing, 0 failing |
| VF2 size/name | PASS | 5,691 bytes (<10KB); dir `rag` == `name: rag` |
| VF3 tier table + golden-set rule + no vendor strings | PASS | tiers 0-3 table present; "Golden set first" before embedding work; `grep -riE "pinecone|weaviate cloud|openai embedding|cohere"` skills/rag -> no matches |
| VF4 claims map to C-numbers | PASS | spot audit: C24 (BM25 overtakes at scale), C36 (FTS5 bm25()/snippet()), C13 (RRF k~60/TREC), C16 (contextual prefixes, flagged [vendor]), C31 (inverted-U), C27 (precision threshold) - all present in rag-practices.md claim map |
| VF5 `python audit.py` -> 0 errors | FAIL (expected) | errors attributable to this change: `disk_only={'rag'}`, `skill_count declared=67 actual=68`, README skills count/badge, TOOLS-MAP skills count |

## VF5 detail

`audit.py` enforces manifest↔disk sync and README/TOOLS-MAP count
invariants. Adding `skills/rag/` necessarily trips those checks, but the
contract boundary forbids editing `manifest.json`, `SKILL-TIERS.md`, and
existing files - wiring is a later contract (consistent with ADR-004:
"manifest + SKILL-TIERS wiring required"). Baseline check (skill dir
temporarily moved aside) shows 4 pre-existing errors unrelated to this
work: TOOLS-MAP.md skills/hook/tool/excluded counts already stale in the
working tree. Re-verify VF5 after the wiring contract lands; the only
rag-caused deltas are the manifest skill entry and count fields.

## Boundary compliance

- No vendor/hosted service or embedding model named as default; model
  selection points at MTEB (C6).
- No runnable code, index, MCP config, or requirements.txt entries; the
  FTS5 shape is described as a table/index shape, not shipped code.
- C29 (arXiv:2608.15008) not cited; the C12 license column is referenced
  only as "re-verify at adoption - flagged unverified", not stated as fact.
- No em-dash (U+2014) - grep-verified. No AI signatures. No build narrative.
- Vendor-flagged claims (C16, C28, bm25s speed) carry their flag markers
  ([vendor], [secondary]) so readers can weight them.

## Notes for orchestrator

- Frozen inputs not re-hashed here (no hash tool invoked); no drift
  observed on read - file lengths matched contract expectations.
- `description` uses "Use when" phrasing covering retrieval, chunking/
  embeddings/vector stores, eval, and the "agent can't find things"
  trigger; `triggers: [user, model]` set.
- CONSULT/ESCALATE: none.
