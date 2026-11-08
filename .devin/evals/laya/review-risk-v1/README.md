# review-risk-v1 calibration run 01 (2026-11-09)

G5 evidence capture for diff-risk triage (4 labels, dict criteria,
live consumer `review_gate.py` shadow suggestion). Production
`.devin/laya/profile.json` remains `mode: off`; capture ran against
`.devin/laya/profile.calibration.json` (mode: shadow).

## Artifacts

- `cases.json` - maintainer-authored draft, 16 labeled cases
  (4 low / 6 medium / 3 high / 3 critical). `snippets` carry the
  exact hint-JSON shape `review_gate._laya_suggestion` emits
  (files_changed, diff_lines, has_tests, q1/q2/q3/q5/q6/q7 flags).
  Golds follow the profile criteria; rr-016 corrected medium->high
  during authoring (no secret/protected/dependency signal).
- `manifest.frozen.json` - real worker replies frozen by
  `capture_eval.py`.
- `report.json` - `eval_decisions.py` metrics.

## Result

| metric | value |
|---|---|
| total | 16 |
| correct | 0 |
| wrong | 0 |
| abstained | 16 |
| accuracy (decided) | n/a |
| coverage | **0.0** |

## Failure modes observed

- **Total abstention on structured state** - `__none__` 16/16,
  `no_match` everywhere, raw_top_probability ~0.15 (uniform). The
  hint-JSON (`{"files_changed":3,"q1":false,...}`) is opaque to a
  semantic text matcher; the model cannot ground boolean flags in
  the criteria prose.
- **State-modality finding** - across all 7 evaluated profiles,
  engagement tracks state *shape*, not just cardinality: prose-ish
  state (issue text, file excerpts, transcripts) produces decisions;
  structured state (flag JSON, action digests) produces uniform
  abstention. If laya is ever used for structured signals, the state
  must be serialized as descriptive prose first.
- **Verdict: not viable as-is** with this checkpoint. Assist stays
  gated; the deterministic flag-vector gate in review_gate.py remains
  the authoritative path (as designed - laya is advisory only).
