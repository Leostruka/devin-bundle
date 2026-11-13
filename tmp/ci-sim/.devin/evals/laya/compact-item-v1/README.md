# compact-item-v1 calibration run 01 (2026-11-09)

Second G5 evidence capture. Production `.devin/laya/profile.json`
remains `mode: off`; capture ran against
`.devin/laya/profile.calibration.json` (mode: shadow).

## Artifacts

- `cases.json` - maintainer-authored draft, 20 labeled cases
  (7 keep / 6 truncate / 5 drop / 2 __none__), state shape mirrors
  `laya-compactor/state.py` (`goal` + `snippets` with
  `kind/name/msg/note` meta header).
- `manifest.pre-criteria.frozen.json` - replies captured BEFORE the
  criteria fix below; kept as defect evidence.
- `report.pre-criteria.json` - metrics for that run (all abstain).
- `manifest.frozen.json` - replies after criteria enrichment.
- `report.json` - `eval_decisions.py` metrics over the frozen manifest.

## Contract fix applied during this run

`compact-item-v1` was the only evaluated profile whose label set was a
plain list of bare verbs (`keep`/`truncate`/`drop`). `build_questions`
turns list labels into criteria by `label.replace("_", " ")` - i.e.
`{"keep": "keep", ...}`, nearly content-free. The model chose `__none__`
on **20/20** cases (`no_match`), coverage 0.0.

Siblings with dict labels (`cmd-risk-v1`, `review-risk-v1`,
`filebool-v1`, `compact-gate-v1`, `compact-boundary-v1`) embed the
semantics directly in criteria. `compact-item-v1` now uses the same
dict shape, text lifted verbatim from its own instructions. Candidate
ids and request envelopes are unchanged; no calibration existed to
invalidate, so the profile keeps the `-v1` name.

## Result (post-fix)

| metric | value |
|---|---|
| total | 20 |
| correct | 1 |
| wrong | 7 |
| abstained | 12 |
| accuracy (decided) | **0.125** |
| coverage | **0.40** |

## Failure modes observed

- **Engagement recovered, judgment did not** - `no_match` dropped
  20→12 and 8 suggestions appeared, but raw_top_probability stayed
  ~0.05–0.25 (near-uniform distribution).
- **keep-attractor** - 7/8 suggestions were `keep`; `truncate`/`drop`
  golds almost never suggested. Retention triage needs session-level
  dependency reasoning ("does a later step reference this?") that a
  per-item classifier cannot see.
- **Verdict: not viable** with this checkpoint. Assist stays gated.
