# knowledge-label-v1 calibration run 01+02 (2026-11-09)

G5 evidence capture for ontology span labeling (8 labels, live
consumer `knowledge_labels.py` attach()). Production
`.devin/laya/profile.json` remains `mode: off`; capture ran against
`.devin/laya/profile.calibration.json` (mode: shadow).

## Contract fix applied during run 01

`knowledge-label-v1` was a plain-list profile whose labels are
ontology jargon (`entity`/`concept`/`relation`/...). `build_questions`
turns list labels into `label.replace("_"," ")` criteria - bare
one-word jargon. Run 01: model chose `__none__` on **16/16** with
HIGH confidence (raw_top_probability 0.47-0.99) - confident
rejection of content-free criteria. Third instance of the defect
class (after compact-item-v1). Converted to dict-labels with ontology
glosses; candidate ids and request envelopes unchanged; `ONTOLOGY`
(frozenset of dict keys - same 8 labels); no calibration existed to
invalidate.

## Artifacts

- `cases.json` - maintainer-authored draft, 16 labeled cases
  (2 per ontology label), realistic project-domain quotes.
- `manifest.pre-criteria.frozen.json` / `report.pre-criteria.json` -
  run 01 defect evidence (16/16 confident abstain).
- `manifest.frozen.json` / `report.json` - run 02 post-fix.

## Result (post-fix, run 02)

| metric | value |
|---|---|
| total | 16 |
| correct | 4 |
| wrong | 0 |
| abstained | 12 |
| accuracy (decided) | **1.000** |
| coverage | **0.25** |

## Failure modes observed

- **Perfect precision, low recall** - every suggestion correct
  (event x2, preference x2); entity/concept/relation/procedure/
  definition/claim all abstained. Decided labels are the ones with
  the most distinctive surface markers (temporal wording,
  "user requires/ prefers" phrasing).
- **Safe failure direction** - abstention leaves spans unlabelled
  (`attach` returns the span copy intact); the model never emits a
  wrong label here. This is the assist-friendly profile shape:
  high-precision suggestions + conservative abstention.
- **Verdict: candidate for calibrated assist** once a threshold is
  bound - unlike every other evaluated profile, wrong=0 means a
  probability gate could adopt suggestions safely. Still requires
  the standard calibration block (id, checkpoint digest, threshold,
  eval id); NOT enabled by this run alone.

## Held-out run (2026-11-09 - 16 fresh spans)

`cases.heldout.json` / `manifest.heldout.frozen.json` /
`report.heldout.json` - fresh spans across all 8 ontology labels,
none reused from run02.

| metric | value |
|---|---|
| total | 16 |
| accuracy (decided) | **0.000** (0/1) |
| coverage | **0.0625** |

The run02 "perfect precision, conservative recall" verdict was a
small-sample artifact: on held-out data the profile abstains 15/16
and its single decision was WRONG (procedure -> event at p=0.48).
Downgraded: NOT viable - the ontology labels do not engage this
checkpoint beyond near-total abstention.
