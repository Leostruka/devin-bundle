# output-context-v1 calibration run 01 (2026-11-09)

Second G5 evidence capture, same protocol as issue-category-v1:
production `profile.json` stays `mode: off`; capture ran against
`profile.calibration.json` (`mode: shadow`).

## Artifacts

- `cases.json` — 20 maintainer-labeled cases (5 runtime_failure /
  4 source_or_documentation / 3 expected_test_failure / 4 warning_only
  / 2 needs_inspection / 2 __none__), request shape mirrors
  `output_context.suggest()` (goal+snippets+app, label candidates).
- `manifest.frozen.json` — real worker replies via `capture_eval.py`.
- `report.json` — `eval_decisions.py` metrics.

## Result

| metric | value |
|---|---|
| total | 20 |
| correct | 9 |
| wrong | 7 |
| abstained | 2 |
| accuracy (decided) | **0.563** |
| coverage | **0.80** |

## Failure mode

**runtime_failure collapse** — 7 of 9 misses picked `runtime_failure`
for source_or_documentation (tsc/mypy/py_compile/eslint), 
expected_test_failure (pytest/jest/unittest), and needs_inspection.
The engine keys on error-shaped surface text ("error", "FAILED",
"warning") and cannot separate compile/test/warning classes from
runtime crashes. Only 2 abstains, both on genuinely thin excerpts.

## Verdict

56% accuracy — **not viable** for the compact_gate JEV-1 lane at
current calibration. Combined with issue-category-v1 (68%), the
evidence says the laya engine handles coarse intent (the earlier
triage preset worked well on open-ended questions) but NOT fine-grained
5-way output taxonomy. Recommendation recorded in issue 04: keep
`mode: off`; revisit after (a) more cases, (b) label-set simplification
(e.g. binary failure-vs-not), or (c) a different checkpoint.

## Reproduce

```bash
cd extensions/laya-tools
.venv/Scripts/python.exe capture_eval.py \
  --draft ../../.devin/evals/laya/output-context-v1/cases.json \
  --config ../../.devin/laya/profile.calibration.json \
  --out ../../.devin/evals/laya/output-context-v1/manifest.frozen.json
.venv/Scripts/python.exe eval_decisions.py \
  --manifest ../../.devin/evals/laya/output-context-v1/manifest.frozen.json \
  --mode evaluate \
  --out ../../.devin/evals/laya/output-context-v1/report.json
```
