# Issue 04: JEV operational patterns rollout

Status: runtime lanes implemented per `LAYA_MASTER_ARCHITECTURE.md` §12;
adoption gated on calibration (G5) - `.devin/laya/profile.json` mode is
`off`, so every lane abstains `feature_off` until enabled.

## Landed

- JEV-1: `compact_gate.eval_floor = 0.25` in `profile.json` and
  `scripts/compact-gate.py` DEFAULTS. Gate emits notices only in `assist`
  mode; it decides, never executes.
- JEV-2: `scripts/skill-picker.py` in the consolidated `user-prompt.py`
  chain - lexical manifest match, max 3 read hints, no daemon call.
- JEV-3: `extensions/laya-tools/explore.py` - rg (or stdlib walk) ->
  batches of 20 via `ask_laya_filebool` -> top-K ranking.
- JEV-4: `extensions/laya-tools/review_gate.py` - 7-question diff triage;
  `review-risk-v1` shadow exists but is not yet in `profile.json.profiles`
  (abstains `feature_off`).
- JEV-5: `extensions/laya-tools/doc_coverage.py` - explicit JSON mapping,
  AST-checked targets under `tests/validation/`; findings are `Important`.
  Shipped map: `.devin/validation-contracts.json`, covered by
  `tests/validation/test_jev_runtime_contracts.py` (11 tests).
- JEV-6: `extensions/computer-use/cu_dom_picker.py` - deterministic
  shortlist (max 8) + staleness checks + `cu_decision` contract; no
  click/dispatch path. `mode` override can only lower the calibrated
  effective mode; `off` abstains `feature_off` without daemon spawn;
  exact-match resolves before the daemon is consulted.

All items respect A1/A3/A8: suggestion or abstain only, cheapest tier
first, deterministic fallback when the daemon is down.

## Open

- Calibration evidence (G5) before enabling `shadow`/`assist`.
- Adding `review-risk-v1` to `profile.json.profiles` when calibrated.
- BitNet adapter evaluation as a decision backend (`ai-tools/`). A real
  native run (`devin-cache/egm-runtime-install/cli_proof2.json`) returned
  `ok:true` with clean output but a semantically wrong completion:
  pipeline executes, model quality and latency NOT established. The older
  240s-timeout smoke is historical, not the current verdict.
