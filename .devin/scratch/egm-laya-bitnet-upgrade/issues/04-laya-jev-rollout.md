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
  **First run landed 2026-11-09**: issue-category-v1, 24 maintainer-
  labeled cases through the real worker (shadow config, production
  profile untouched). Result: accuracy 0.684 / coverage 0.792 /
  abstain_precision 0.20 - BELOW assist threshold. Failure modes:
  abstain bias on terse technical text, needs_info blindness
  (surface bug semantics beat triage convention), __none__ misses on
  multi-intent text. Evidence + reproduce steps:
  `.devin/evals/laya/issue-category-v1/`. No calibration block
  written; mode stays `off`. Next: second annotator pass on the
  needs_info golds + more cases per profile before re-eval.
  **Second run same day**: output-context-v1, 20 cases - accuracy
  0.563 / coverage 0.80. Failure mode: runtime_failure collapse
  (7/9 misses) - engine keys on error-shaped surface text and cannot
  separate compile/test/warning classes. Combined evidence: coarse
  intent OK, fine-grained taxonomy NOT viable. Options recorded:
  more cases, simplified label sets, or different checkpoint.
  Artifacts: `.devin/evals/laya/{issue-category-v1,output-context-v1}/`.
  **Third run**: skill-family-v1, two drafts - run01 dev-flavored
  goals acc 0.125 (eval-design flaw: dev vocabulary legitimately
  reads as development), run02 cross-domain goals acc 0.421. Cross-
  profile pattern: accuracy degrades with label cardinality
  (3-way 0.68 / 5-way 0.56 / 7-way 0.42). Viable paths: shrink label
  sets to <=3, binary reformulations, or different checkpoint.
  Artifacts: `.devin/evals/laya/skill-family-v1/`.
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
  **<=3-label sweep completed same day** (the documented viable path):
  compact-item-v1, filebool-v1, compact-boundary-v1 - 52 cases total.
  - compact-item-v1: exposed a real contract defect - list labels
    produced content-free criteria ({"keep":"keep"}), model abstained
    20/20. Fixed to dict-labels (sibling pattern); engagement
    recovered (8 decided) but accuracy 0.125, keep-attractor. NOT
    viable: retention triage needs session-dependency reasoning.
  - filebool-v1: acc 0.444 / cov 0.5625 - yes-collapse (all 9
    suggestions "yes"; every no-gold abstained or erred). Code
    comprehension beyond checkpoint.
  - compact-boundary-v1: 16/16 abstain, coverage 0.0 - trajectory
    classification needs temporal reasoning.
  Meta-pattern across ALL 6 evaluated profiles: only
  issue-category-v1 (surface-feature triage, 0.684) approaches
  viability. Cardinality matters less than task type - anything
  requiring comprehension, session state, or fine taxonomy fails.
  Assist gate stays closed; next lever is a different checkpoint,
  not more cases on this one.
  Artifacts: `.devin/evals/laya/{compact-item-v1,filebool-v1,
  compact-boundary-v1}/`.
  **review-risk-v1 run same day** (4th <=3-label-adjacent profile,
  dict criteria, live consumer review_gate.py): 16 cases, coverage
  0.0 - total abstention. Root cause is STATE MODALITY, not labels:
  the hint-JSON flag vector is opaque to a semantic text matcher.
  Meta-pattern refined across all 7 evaluated profiles: engagement
  tracks state shape - prose state (issue text, file heads,
  transcripts) decides; structured state (flag JSON, digests)
  abstains uniformly. If structured signals are ever routed to laya,
  serialize them as descriptive prose in `snippets` first.
  Artifacts: `.devin/evals/laya/review-risk-v1/`.
  **cmd-risk-v1 run same day** (5 labels, dict criteria, the ONLY
  consumer that can BLOCK in assist - laya-guard.py): exposed a real
  contract bug first - guard sent goal:"" so every request was
  invalid_request:state_goal_invalid (lane silently dead since
  authoring). Fixed goal text; recaptured: acc 0.231 / cov 0.65.
  Failure mode is disqualifying for a safety gate: irreversible ->
  mutating/abstain (never irreversible), id_rsa -> mutating,
  git push -> benign. Deterministic feats vector stays authoritative.
  Artifacts: `.devin/evals/laya/cmd-risk-v1/` (+invalid-goal manifest).
  **knowledge-label-v1 runs same day** (8 labels, live consumer
  knowledge_labels.py): run01 exposed the THIRD instance of the
  bare-list-criteria defect - ontology jargon produced content-free
  criteria, model confidently abstained 16/16 (p 0.47-0.99). Fixed to
  dict-labels with ontology glosses; run02: accuracy 1.000 on 4
  decided / coverage 0.25 - perfect precision, conservative recall,
  SAFE failure direction (abstain = span stays unlabelled, never
  wrong). First profile shaped like a viable high-precision assist
  candidate - still needs the standard calibration block (threshold,
  checkpoint digest, eval id); NOT enabled by this run.
  Artifacts: `.devin/evals/laya/knowledge-label-v1/`.
  **media-intent-v1 BREAKTHROUGH same day** (5 labels, live consumer
  media-tools/intent.py): first genuinely viable profile - run01
  acc 1.000/cov 0.813, run02 acc 0.938/cov 0.667 (28/29 decided
  correct). Works because intents are distinct workflow destinations
  matched on natural-language state - the checkpoint's strength.
  Platt fit on frozen replies: a=23.1982 b=-13.1611, thr 0.9 ->
  27/29 adopted at 1.000 (same-data). HELD-OUT run03 (20 fresh
  cases): acc 0.857, adopted@0.9 = 9/10 (0.90) - fit was optimistic;
  one complaint ("the video looks weird") adopted wrongly at conf
  0.945 and platt saturates so no threshold separates it. Verdict:
  only viable assist candidate, shadow-only pending more held-out
  evidence + non-saturating map + deliberate activation steps.
  Artifacts: `.devin/evals/laya/media-intent-v1/` (3 runs).
  **CAMPAIGN COMPLETE same day - all 14 profiles evaluated**
  (~250 frozen cases through the real worker):
  - media-intent-v1: 0.966 decided acc, held-out adopted 0.90 -
    ONLY viable assist candidate (shadow-only pending evidence).
  - media-preset-v1: 0.875/0.50 - borderline, thin n.
  - issue-category-v1: 0.684/0.79 - best fixed-label triage.
  - knowledge-label-v1: 1.000/0.25 - perfect precision, low recall.
  - skill-pick-v1: 1.000/0.133 - extreme abstention + flaky
    engine_error:TypeError (transient, fail-safe held).
  - ui-target-v1: 0.714/0.70 - DANGEROUS __none__ commits for a
    click gate.
  - filebool-v1: 0.444 yes-collapse; output-context-v1: 0.563
    collapse; skill-family-v1: 0.421 cardinality; cmd-risk-v1:
    0.231 unsafe direction; compact-item-v1: 0.125;
    compact-boundary-v1 + compact-gate-v1 + review-risk-v1: 0/0
    abstention (trajectory/structured state).
  Contract fixes landed: compact-item + knowledge-label dict-labels
  (bare-list criteria defect, 2 more instances), laya-guard empty-goal
  dead lane. Meta-laws: prose state decides, structured abstains;
  natural-language intents match, comprehension/trajectory fails.
  Assist remains OFF everywhere; only media-intent has a credible
  path (more held-out + non-saturating map + deliberate activation).
  **Held-out batch 2 (run 04, +20 fresh cases)**: acc 0.929
  decided, adopted@0.9 = 13/13 (1.000 this batch; the one wrong
  pick p=0.594 correctly rejected by the gate). Combined held-out
  (40 cases never in the fit): adopted 23, correct 22 -> 0.9565;
  sole wrong adoption still mi-h14 complaint->stylize_video.
  Failure mode pinned: media complaints/observations phrased as
  non-imperatives. Evidence now: 80 decided cases total, 40
  strictly held-out. Activation checklist unchanged; mode stays
  off/shadow. Artifacts: manifest.heldout2.frozen.json,
  report.heldout2.json, cases.heldout2.json.
