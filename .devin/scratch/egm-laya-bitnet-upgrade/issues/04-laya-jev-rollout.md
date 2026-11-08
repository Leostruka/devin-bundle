# Issue 04: JEV operational patterns rollout

Status: runtime lanes implemented per `LAYA_MASTER_ARCHITECTURE.md` §12;
adoption gated on calibration (G5) - `.devin/laya/profile.json` mode is
`off`, so every lane abstains `feature_off` until enabled.

estimate_min: 120

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
- BitNet adapter evaluation as a decision backend (`ai-tools/`).
  Measured 2026-11-09 (runtime at
  `~/AppData/Local/devin-cache/egm-runtime-install/`, binary
  `BitNet/build/bin/llama-cli.exe` - the prebuilt `llama-bin/` binary
  cannot read the ternary model: TYPE_IQ4_NL_4_4 removed):
  - Latency: generation **35.4 tok/s**, prompt 113.8 t/s, 8 threads,
    ggml-model-i2_s.gguf (1.58-bit ~2B).
  - Quality: **FAIL** - 3/3 probes degenerate into repetition loops
    ("The capital of France is a capital of France...", prompt
    echo loops); never produces a coherent answer. Consistent with
    cli_proof2's semantically-wrong completion.
  - Verdict: pipeline executes and is fast enough for suggestion-tier
    latency, but this model size/quant is NOT viable as a decision
    backend. Options: larger BitNet variant (i2_m?), or keep laya as
    the only decision model and drop the BitNet lane.
