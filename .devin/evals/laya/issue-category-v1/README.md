# issue-category-v1 calibration run 01 (2026-11-09)

First G5 evidence capture for the laya decision backend. Production
`.devin/laya/profile.json` remains `mode: off`; capture ran against
`.devin/laya/profile.calibration.json` (identical except `mode: shadow`).

## Artifacts

- `cases.json` — maintainer-authored draft, 24 labeled cases
  (8 bug / 8 enhancement / 4 needs_info / 4 __none__).
- `manifest.frozen.json` — real worker replies frozen by
  `capture_eval.py` (one resident worker, cold load paid once).
- `report.json` — `eval_decisions.py` metrics over the frozen manifest.

## Result

| metric | value |
|---|---|
| total | 24 |
| correct | 13 |
| wrong | 6 |
| abstained | 4 (+1 correct_abstain) |
| accuracy (decided) | **0.684** (Wilson low 0.496) |
| coverage | **0.792** |
| abstain_precision | 0.20 |

## Failure modes observed

- **Abstain bias on terse technical text** — ic-001/ic-006 (clear bugs
  with traceback/encoding detail) abstained; ic-012/ic-020 likewise.
  Engine is conservative where gold expects commitment.
- **needs_info blindness** — ic-017/018/019 ("tool is broken",
  "doesn't work sometimes", "render is slow") classified `bug`.
  Surface semantics favor bug; triage convention wants info first.
  Partially a label-convention gap, not pure engine error — a second
  annotator could defensibly label these `bug`.
- **__none__ misses** — ic-021/023/024 (multi-intent or question-shaped
  text) still committed to bug/enhancement despite the profile's
  "choose __none__ when unclear" instruction.

## Verdict

68% accuracy / 79% coverage is **below any reasonable assist
threshold**. issue-category-v1 stays gated: no `calibration` block was
written to profile.json, mode stays `off`. Evidence supports the
design (typed abstention works, failures are honest abstains/wrongs,
never fabricated certainty) but not activation.

## Reproduce

```bash
cd extensions/laya-tools
.venv/Scripts/python.exe capture_eval.py \
  --draft ../../.devin/evals/laya/issue-category-v1/cases.json \
  --config ../../.devin/laya/profile.calibration.json \
  --out ../../.devin/evals/laya/issue-category-v1/manifest.frozen.json
.venv/Scripts/python.exe eval_decisions.py \
  --manifest ../../.devin/evals/laya/issue-category-v1/manifest.frozen.json \
  --mode evaluate \
  --out ../../.devin/evals/laya/issue-category-v1/report.json
```
