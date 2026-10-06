# Handoff: 07-reviewer-rag-skill

## Result

- **Status:** DONE - review complete; verdict **FIX: [S1]** (one Important,
  one Minor; see `.devin/research/rag-skill-review.md`)

## Files written

- `.devin/research/rag-skill-review.md` (review report, VERDICT line at :3)
- `.devin/handoffs/07-reviewer-rag-skill-out.md` (this file)

No other files modified (read-only lane honored; two exec misfires produced
no writes - verified review file content after rewrite).

## VF results (contract 07)

| VF | Result | Evidence |
|---|---|---|
| VF1 review file exists with VERDICT line | PASS | `.devin/research/rag-skill-review.md:3` - `VERDICT: FIX: [S1]` |
| VF2 every FIX item cites file:line + rule/C-number | PASS | S1 cites eval-and-failures.md:11 + contract-05 traceability clause + rag-practices.md:407-409; S2 cites SKILL.md:57 + C36 vs rag-practices.md:409-411 |
| VF3 boundary sentences for >=3 neighbors | PASS | 4 sentences: research, knowledge-modeling, memory-management, context7 (review :77-93) |

## Findings summary

- **S1 (Important):** `skills/rag/reference/eval-and-failures.md:11` -
  "30+ pairs minimum" is a fixed numeric threshold with no C-number;
  no golden-set size floor exists in the research; self-quiz 2a
  (rag-practices.md:407-409) forbids fixed numeric thresholds. Violates
  contract-05 "every practice must trace to a C-number". Fix: drop the
  number or mark it heuristic.
- **S2 (Minor):** `skills/rag/SKILL.md:57` - "(C36)" over-covers the
  FTS5-compiled feature-check; platform-dependence lives in uncited
  self-quiz 2b. Practice correct; citation loose. Same statement in
  tier-recipes.md:37-40 is correctly uncited.

## Axes

- **Standards: PASS.** Frontmatter triggers clean; 5,691 B <= 10KB;
  pointers resolve; telegraphic; no vendor default; zero non-ASCII (no
  em-dash); no AI signature; `validate-skill-format.py skills` -> rag
  PASS score 100 (68/68).
- **Spec: FIX.** All contract-05 content requirements present; 30+
  C-citations audited, all trace correctly with flags carried; C29
  absent as required; only S1 breaks traceability.

## Evidence highlights

- Frozen hashes verified: rag-practices.md=04960e75..., SKILL.md=d6a765bb...
  (both match contract-07).
- grep vendor-defaults/AI-signature scan: clean.
- python byte-scan for U+2014 and all non-ASCII: 0 hits in all 3 files.

## Notes for orchestrator

- Sharpest trigger collision is rag vs research ("can't find things in
  docs" vs "exploration beyond a quick grep"); boundary sentence written
  (review :77-81) - discriminator is perform-search-now vs
  build-retrieval-capability.
- CONSULT/ESCALATE: none. Implementer's VF5 concern (audit.py wiring
  counts) is a contract-06 matter, not a skills/rag/ content defect.
