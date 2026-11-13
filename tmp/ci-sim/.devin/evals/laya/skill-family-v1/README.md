# skill-family-v1 calibration runs 01+02 (2026-11-09)

Third G5 evidence capture. Two drafts because run 01 exposed an eval-
design flaw (see below). Production `profile.json` stays `mode: off`;
capture used `profile.calibration.json` (`mode: shadow`).

## Run 01 — dev-flavored goals (cases.json)

24 cases, all goals written in software-engineering vocabulary.

| metric | value |
|---|---|
| accuracy | **0.125** |
| coverage | 0.667 |

Engine picked `development` for nearly everything — initially read
as catastrophic failure.

## Run 02 — cross-domain goals (cases.v2.json)

Same 7 families, goals rewritten to genuinely cross-domain tasks
(sales CSV, Lisbon itinerary, workout routine, logo design...).

| metric | value |
|---|---|
| accuracy | **0.421** |
| coverage | 0.792 |

Still fails, but the delta (12.5% -> 42%) proves run 01's gold labels
were partly unfair: dev-vocabulary goals legitimately read as
development tasks. Run 02 is the honest measurement.

## Failure mode (run 02)

`development` remains the attractor (5 misses), with investigation/
data/visual/knowledge bleeding into development or operations.
Non-technical assistance tasks abstain or misroute. The 7-way family
taxonomy exceeds what this checkpoint separates reliably.

## Cross-profile G5 picture (all 2026-11-09)

| profile | labels | accuracy | coverage | verdict |
|---|---|---|---|---|
| issue-category-v1 | 3+none | 0.684 | 0.792 | below threshold |
| output-context-v1 | 5+none | 0.563 | 0.800 | runtime_failure collapse |
| skill-family-v1 | 7+none | 0.421 | 0.792 | development collapse |

**Pattern: accuracy degrades with label cardinality.** The checkpoint
handles ~3-way coarse distinctions marginally; 5-7-way taxonomies
collapse to the most frequent surface class. Recommendation (issue
04): keep `mode: off`; viable paths are (a) shrink label sets to
<=3 options per profile, (b) binary reformulations (failure-vs-not,
mutating-vs-not), or (c) a different/stronger checkpoint. Shadow-only
deployment remains safe by design (suggestion-or-abstain, deterministic
fallback) if partial coverage is ever wanted.

## Reproduce

```bash
cd extensions/laya-tools
.venv/Scripts/python.exe capture_eval.py \
  --draft ../../.devin/evals/laya/skill-family-v1/cases.v2.json \
  --config ../../.devin/laya/profile.calibration.json \
  --out ../../.devin/evals/laya/skill-family-v1/manifest.v2.frozen.json
.venv/Scripts/python.exe eval_decisions.py \
  --manifest ../../.devin/evals/laya/skill-family-v1/manifest.v2.frozen.json \
  --mode evaluate \
  --out ../../.devin/evals/laya/skill-family-v1/report.v2.json
```
