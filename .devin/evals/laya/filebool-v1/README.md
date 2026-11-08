# filebool-v1 calibration run 01 (2026-11-09)

G5 evidence capture for the boolean file-classification profile
(2 labels, dict criteria - the cleanest formulation in the contract).
Production `.devin/laya/profile.json` remains `mode: off`; capture ran
against `.devin/laya/profile.calibration.json` (mode: shadow).

## Artifacts

- `cases.json` - maintainer-authored draft, 16 labeled cases
  (8 yes / 8 no). Snippets are REAL 700-char file heads from this
  repo; golds verified directly against the excerpt text.
- `manifest.frozen.json` - real worker replies frozen by
  `capture_eval.py`.
- `report.json` - `eval_decisions.py` metrics.

## Result

| metric | value |
|---|---|
| total | 16 |
| correct | 4 |
| wrong | 5 |
| abstained | 7 |
| accuracy (decided) | **0.444** |
| coverage | **0.5625** |

## Failure modes observed

- **yes-collapse** - all 9 suggestions were `yes`. Every `no` gold
  either abstained (6) or was wrongly suggested `yes` (fb-004,
  fb-006, fb-011, fb-015). Binary file questions degenerate to the
  affirmative prior.
- **Comprehension gap** - questions like "does this file spawn
  subprocesses?" require reading imports/usage across the head; the
  model pattern-matches surface tokens instead.
- **Verdict: not viable** with this checkpoint. Assist stays gated.

## UTF-8 recapture (2026-11-09)

7/16 cases carried non-ASCII file-head text; under the pre-fix
worker (cp1252 stdio) those decoded to mojibake without crashing
(cp1252-representable chars) - silently degraded, not errored.
Post-fix recapture (`manifest.utf8.frozen.json` /
`report.utf8.json`): accuracy 0.500 / coverage 0.500 - yes-collapse
persists (all 8 suggestions still `yes`). Verdict unchanged: not
viable; the recapture makes the evidence clean rather than
mojibake-contaminated.
