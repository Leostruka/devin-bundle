# media-intent-v1 calibration runs 01+02 (2026-11-09)

G5 evidence capture for media workflow-intent routing (5 labels,
live consumer `media-tools/intent.py` - suggestion-only, names an
existing workflow/preset for preview; never writes output, params,
camera, overwrite or delete). Production `.devin/laya/profile.json`
remains `mode: off`; captures ran against
`.devin/laya/profile.calibration.json` (mode: shadow).

## Why this profile works when others fail

- Intents are DISTINCT workflow destinations with clear semantic
  boundaries (image-stylize vs video-stylize vs diagram vs
  launch-video vs ui-design) - the checkpoint's surface-matching
  strength, not comprehension.
- State is the raw user request text in `goal` - natural language,
  the modality this engine handles (contrast: flag-JSON and digests
  abstain uniformly - see review-risk-v1/compact-boundary-v1).
- snake_case labels render as descriptive criteria
  ("stylize image", "launch video") - sufficient gloss.

## Artifacts

- `cases.json` / `manifest.frozen.json` / `report.json` - run 01,
  16 cases (5 stylize_image / 3 stylize_video / 3 diagram /
  3 launch_video / 2 ui_design).
- `cases.v2.json` / `manifest.v2.frozen.json` / `report.v2.json` -
  run 02, 24 cases with diverse phrasing + 6 `__none__` ambiguous
  controls ("make it look cooler", "edit this file for me", ...).

## Results

| run | total | correct | wrong | abstained | accuracy | coverage |
|---|---|---|---|---|---|---|
| 01 | 16 | 13 | 0 | 3 | **1.000** | 0.813 |
| 02 | 24 | 15 | 1 | 8 | **0.938** | 0.667 |
| combined | 40 | 28 | 1 | 11 | **0.966** | 0.725 |

## Failure modes observed

- **Single wrong on maximally ambiguous input** - mi-028 "make it
  look cooler" -> ui_design (gold __none__). Borderline gold; the
  other 5 ambiguous controls abstained correctly (p 0.61-0.99 on
  __none__).
- **Deadline misses** - 1 case (mi-001) hit deadline_exceeded; cold
  CPU inference occasionally exceeds the 1000ms request budget.
- **Abstain precision is good** - decided cases carry p 0.6-1.0;
  wrong answers do not hide among high-confidence picks.

## Verdict: FIRST viable assist candidate

96.6% accuracy on decided cases with safe abstention. Assist
activation still requires the full contract: calibration block
(id, checkpoint_sha256, profile, locale, data_source, evaluation_id,
threshold, candidate cardinality) AND a fitted probability map -
without a map `_calibrated()` returns None and `adoptable` can never
be true. NOT enabled.

## Calibration proposal (fitted 2026-11-09, for review - NOT applied)

Platt fit on the 29 decided frozen replies (raw_confidence ->
correct): `a=23.1982, b=-13.1611`. The single wrong case sat at the
minimum confidence (0.518); the map separates it cleanly.

| threshold | adopted | adopted accuracy |
|---|---|---|
| 0.5-0.8 | 28/29 | 1.000 |
| **0.9** | **27/29** | **1.000** |
| 0.95 | 27/29 | 1.000 |

Recommended block shape (still needs `models.<name>.sha256` of the
real checkpoint and `profiles` += `media-intent-v1` before mode can
leave off/shadow):

```json
"calibration": {
  "id": "media-intent-v1-cal-2026-11-09",
  "checkpoint_sha256": "<digest of approved checkpoint>",
  "profile": "media-intent-v1",
  "locale": "en",
  "data_source": ".devin/evals/laya/media-intent-v1/",
  "evaluation_id": "media-intent-v1-cal-01+02",
  "threshold": 0.9,
  "cardinality": 5,
  "map": {"kind": "platt", "a": 23.1982, "b": -13.1611}
}
```

Caveat: n=29 decided is modest; Wilson low on 28/29 ~0.83. The map
was fit on the same data it would gate - a held-out confirmation
run (fresh cases) is the honest next step before any mode flip.

## Held-out confirmation (run 03, 2026-11-09 - 20 fresh cases)

`cases.heldout.json` / `manifest.heldout.frozen.json` /
`report.heldout.json` - phrasings NOT used in the Platt fit.

| metric | value |
|---|---|
| total | 20 |
| accuracy (decided) | 0.857 |
| coverage | 0.70 |
| adopted @ cal_p>=0.9 | 10 |
| adopted correct | 9 |
| **adopted accuracy** | **0.90** |

Held-out verdict: the same-data fit was optimistic (1.000 -> 0.90
adopted). One wrong adoption: mi-h14 "the video looks weird" (a
complaint, gold __none__) -> stylize_video at conf 0.945; the Platt
map saturates ~1.0 for conf>0.9 so no threshold separates it.
Correct suggestions below threshold (calp 0.67-0.86) show the gate
is conservative where it matters.

**Recommendation stands but weaker**: media-intent remains the only
viable assist candidate, shadow-only for now. Before any mode flip:
(more held-out cases to tighten the Wilson bound), consider raising
threshold to 0.95+ AND/OR a table map that does not saturate, plus
the deliberate activation steps (models sha256, profiles +=
media-intent-v1, mode assist). NOT enabled.

## Held-out batch 2 (run 04, 2026-11-09 - 20 more fresh cases)

`cases.heldout2.json` / `manifest.heldout2.frozen.json` /
`report.heldout2.json` - second batch of phrasings never used in the
Platt fit; includes complaint/question/ambiguous `__none__` traps
("the export is taking forever", "why did the render fail?",
"make it pop").

| metric | value |
|---|---|
| total | 20 |
| accuracy (decided) | 0.929 (13/14) |
| coverage | 0.70 |
| adopted @ cal_p>=0.9 | 13 |
| adopted correct | 13 |
| **adopted accuracy (this batch)** | **1.000** |

The single wrong decision (mi-h40 "make it pop" -> ui_design, raw
p 0.594) is correctly rejected by the gate (cal_p ~0.65 < 0.9).

## Combined held-out evidence (40 fresh cases)

| metric | value |
|---|---|
| adopted @ cal_p>=0.9 | 23 |
| adopted correct | 22 |
| **adopted accuracy** | **0.9565** |
| wrong adoptions | 1 (mi-h14 complaint -> stylize_video) |
| adopted coverage | 23/40 = 0.575 |

Failure mode is now precisely characterized: media complaints /
observations ("the video looks weird") get mapped to stylize_video.
Requests phrased as observations rather than imperatives are the
residual risk. A consumer-side guard (only route imperative user
requests) or a table map with a non-saturating shoulder would both
reduce it; neither is applied.

Verdict unchanged: strongest assist candidate by far, still
shadow-only pending the deliberate activation checklist above.

## Calibration-map bake-off (fit_calibration.py, 2026-11-09)

`extensions/laya-tools/fit_calibration.py` fits platt + isotonic
table maps on the 29 train decided cases (runs 01+02) and scores
adoption curves on both held-out batches. Report:
`calibration-fit.json`.

| map @ thr 0.9 | adopted | correct | acc | notes |
|---|---|---|---|---|
| platt a=23.1982 b=-13.1611 (earlier fit) | 23 | 22 | 0.9565 | saturates ~1.0 above p~0.79 |
| platt a=186.5 b=-107.9 (NR refit) | 27 | 25 | 0.9259 | near-separable train -> step at p~0.58 |
| table (PAVA isotonic) | 24 | 23 | **0.9583** | non-saturating, graded |

All maps land within Wilson noise; none separates the wrong
adoptions (mi-h14 p=0.945, mi-h40 p=0.594 sit inside every adopt
region). Conclusion: the residual risk is a MODEL limitation, not a
calibration limitation - no map fixes it. Mitigation must be
consumer-side (imperative-only routing guard) or accept the ~4%
wrong-adoption rate. The isotonic table is the best structural
candidate if activation proceeds (graded probabilities, rejects
borderline picks).
