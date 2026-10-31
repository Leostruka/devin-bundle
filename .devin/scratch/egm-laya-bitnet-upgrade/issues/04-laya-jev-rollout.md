# Issue 04: JEV operational patterns rollout

Status: design landed in `LAYA_MASTER_ARCHITECTURE.md` §12; implementation
is future work ordered by LAYA §10.

## Tickets when scheduled

- JEV-1: `profile.json` `compact_gate.eval_floor` 0.50 -> 0.25.
- JEV-2: skill picker pre-filter in `user-prompt.py` (stdlib-only, lexical,
  no Laya on the hot path).
- JEV-3: two-stage explore (ripgrep -> `ask_laya_filebool` batch of 20 ->
  top-K) wired into `laya-orchestrator` skill.
- JEV-4: 7-question pre-review gate feeding `review-risk-v1` hints.
- JEV-5: doc-to-test coverage check surfaced in reviewer output.
- JEV-6: DOM action picker via `cu_decision.py` candidates path.

All items respect A1/A3/A8: suggestion or abstain only, cheapest tier first,
deterministic fallback when the daemon is down.
