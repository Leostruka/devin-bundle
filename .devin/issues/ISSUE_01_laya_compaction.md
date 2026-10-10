# ISSUE 01, Intelligent Context Compaction: `laya` ("Smart Window")

Status: superseded-by `.devin/research/LAYA_MASTER_ARCHITECTURE.md` · Source: upstream MIT compaction port · Ledger: `.devin/research/4_fronts_recon.md`

## Contexto & Valor

- Upstream replaces lossy summarization with **per-item keep/truncate/drop decisions**: every `tool_use`/`tool_result` is scored by a System-1 decision model; survivors stay **verbatim**, file paths, errors, constraints never get reworded away.
- Upstream engine = hosted decision model over a paid SaaS API. Our `laya` is the same primitive class: non-autoregressive, `noul` questions = P(true), ~200-460 ms CPU, offline, free. Port = same behavior, zero API dependency, integrates with the existing `laya-tools` worker/contract (off→shadow→assist).
- Value: cheaper + deterministic compaction, no summary distortion, composable with `context-folding` (fold = keep everything offloaded; compact = prune dead tool noise).

## Smart Window, valores recomendados

Adaptive effective window, not fixed recency:

| Param | Value | Basis |
|---|---|---|
| `compact_at` | 0.70 × model window (SWE-2 262k → ~183k) | Haystack default; keeps headroom for next tool batch |
| `compact_to` | 0.40 × window (~105k) | hysteresis: defers next compaction, avoids thrash |
| `preserve_recent` | 6 messages + first message | upstream port default |
| `keep_threshold` | 0.5 → calibrate on our transcripts | upstream port default; laya confidence is entropy-based, measure, don't copy |
| `truncate_head` | 300 chars | upstream port default |
| `max_state` | ~25k est. tokens | fits laya context comfortably |
| `reduction_floor` | <0.25 → abort, keep original | avoids pointless churn |

## Brain (Skill)

- **Update `context-folding`** + `context-hygiene`: add the prune-vs-fold-vs-summarize decision table; document Smart Window params above.
- Decision policy lives in the skill: what to pin (system/first/last user task + newest N), when to abstain (laya `assist` mode requires `activation_errors` empty + calibrated threshold), escalation to `compact` summary only when pruning can't reach `compact_to`.

## Muscle (Extension)

`extensions/laya-compactor/` (Python, reuses `laya-tools` worker via `decision_client`):

- `transcript.py`, parse session messages → pair `tool_use`/`tool_result`, pin set.
- `state.py`, build decision state (results → `ok, N chars` notes) + staged fitting (inputs 1000→200→60, head+tail abridged, message collapse) to `max_state`.
- `questions.json`, `{"keep_call": {"type":"noul","instructions":"..."}, "keep_result": {"type":"noul","instructions":"..."}}`.
- `compact.py` CLI, transcript JSON → pruned JSON + `decisions` + `stats`; batches `noul` calls through resident `laya_worker` (no per-call reload); honors contract modes.
- Fallback contract: laya error / malformed / under-reduction → return original unchanged.

## Step-by-step (on authorization)

1. Port `collectToolCalls`/`fitState`/`decideCall`/`applyDecisions` from upstream `src/` (MIT) → Python modules above. Preserve stage order and thresholds.
2. Wire `laya_worker` resident process; add compactor profile to `decision_contract` (`suggestion`/`abstain` only, never `allow`).
3. Gate G1: replay upstream `examples/` transcripts → decisions ≥ agreed; `reductionRatio` reported.
4. Gate G2: golden set, 5 real Devin session transcripts; assert: no orphan `tool_result`, pinned untouched, verbatim survivors byte-identical.
5. Gate G3 (held-out per Rule 15): retention test, run a downstream task from compacted transcript, verify referenced paths/commands still resolvable.
6. Shadow mode → measure → calibrate `keep_threshold` → promote to `assist`.

## Non-goals

No summarizer, no upstream TypeSafe API dependency, no Rust crate (Python is fast enough; revisit per ADR-003 only if profiled hot).
