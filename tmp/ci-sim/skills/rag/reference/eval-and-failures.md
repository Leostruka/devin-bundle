# RAG evaluation sketch and failure catalog

C-numbers cite `.devin/research/rag-practices.md`.

## Eval layer 1: deterministic retrieval eval (build this first)

Standard practice: label golden passages, measure retrieval against
them before tuning anything else (C18 - used by both the Chroma
chunking report and the contextual-retrieval cookbook).

**Golden set.** Size it to your corpus, not a fixed count: cover each
distinct intent in the corpus plus paraphrase and adversarial cases, and
grow it over time as real failures surface:

```json
{"query": "how are skills synced to the manifest",
 "expected": [{"path": "manifest.json", "line_hint": "skills list"}]}
```

Collect real failed questions from users/agents - they are the highest-
value entries. Paraphrase each query once so the set tests lexical and
semantic legs separately.

**Metrics** (all computable in stdlib):

- Hit rate: fraction of queries where any expected passage appears in
  top-k.
- Recall@k: fraction of expected passages retrieved in top-k.
- MRR: mean of `1/rank` of the first expected hit.
- Pass@k where the retriever feeds a downstream agent.

Run it against the current tier before every escalation; a passing
score on tier 0/1 is the de-escalation signal (C24, C25). Retrieval
below a precision threshold actively degrades agent performance - one
study needed ~0.68 precision before retrieval bought efficiency, and a
0.38-precision retriever hurt (C27 [abs]; treat numbers as directional).

## Eval layer 2: answer-quality eval (second, optional)

- Reference-free frameworks exist for faithfulness, answer relevance,
  context precision/recall (RAGAS family, C17).
- LLM judges are unreliable ungrounded: agreement improves when you
  supply a human-written reference answer - a weaker judge with a good
  reference beats a stronger judge with a synthetic one (C19 [abs]);
  no debiasing method cuts required labels by more than half when the
  judge is no better than the system under test (C20 [abs]); large
  judge studies found universal agreement deflation and position bias
  (C21 [abs]).
- Practical rule: human spot-check the cases where judge and data
  disagree; never gate on judge output alone.

## Failure catalog

| Symptom | Likely failure | Fix lever | Evidence |
|---|---|---|---|
| Answer not in corpus at all | FP1 missing content | ingest more sources / say "unknown" | C34 |
| Present but never ranked | FP2 missed top rank | chunking, fusion, more candidates | C34 |
| Retrieved but ignored in context | FP3 not consolidated | fewer chunks; best at edges | C31, C33 |
| Right chunk, answer not extracted | FP4 | prompt, chunk size | C34 |
| Wrong output shape | FP5 wrong format | output contract in prompt | C34 |
| Too vague / too specific | FP6 specificity | rerank, context sizing | C34 |
| Partial answer | FP7 incomplete | iterate retrieval, higher recall@k | C34 |
| Quality decays as chunks added | inverted-U over-fetch | tune k; rerank down | C31 |
| Worst chunk sits mid-context | position effect | order best at beginning/end | C33 |
| Accuracy collapses on huge contexts | >~64k decay in most models | cap retrieved volume | C32 [abs] |
| Agent slower/worse with retrieval on | below precision threshold | raise precision or drop retrieval | C27 [abs] |
| Loop spirals, errors compound | agentic-loop risks | bound iterations, verify each hop | C23 [abs] |
| Index answers stale after edits | drift / dup entries | rebuild or merge with provenance hashes | C34 family |
| Eval looks great but users disagree | judge bias | human references, spot-checks | C19-C21 |

RAG validation is only feasible during operation - robustness evolves
rather than being designed in upfront, so keep the golden set growing
from real failures (C34).
