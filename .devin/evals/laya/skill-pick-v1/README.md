# skill-pick-v1 calibration run 01 (2026-11-09)

G5 evidence capture for skill selection (dynamic candidates - the
real manifest catalog shortlists per family, exactly as
`workflow_routing.recommend` builds them: id/name + purpose[:200]
as scope). Live consumer: `workflow_routing.py` stage 2.
Production `.devin/laya/profile.json` remains `mode: off`; capture
ran against `.devin/laya/profile.calibration.json` (mode: shadow).

## Artifacts

- `cases.json` - maintainer-authored draft, 30 labeled cases across
  all 7 families (24 skill picks / 6 __none__ controls where the
  family shortlist genuinely lacks a fit).
- `manifest.frozen.json` - real worker replies frozen by
  `capture_eval.py`.
- `report.json` - `eval_decisions.py` metrics.

## Result

| metric | value |
|---|---|
| total | 30 |
| correct | 4 |
| wrong | 0 |
| abstained | 26 |
| accuracy (decided) | **1.000** |
| coverage | **0.133** |

## Failure modes observed

- **Extreme abstention on 8-candidate sets** - decided only 4/30
  (all assistance/knowledge families with shorter purposes);
  development/investigation/operations/visual shortlists produced
  `no_match` nearly always. Long purpose texts as criteria do not
  engage the matcher.
- **Transient engine_error** - 4 cases returned
  `engine_error:TypeError` (sp-008/014/020/025). Re-running sp-008
  standalone reproduces a clean `__none__` distribution - the error
  is flaky inside the resident worker, not request-deterministic.
  Fail-safe held: typed abstain, never a wrong suggestion. Worth a
  worker-stability note; the broad `except` hides the real
  traceback on stderr.
- **Verdict: not viable as-is** - perfect precision but 13% coverage
  means the routing lane would almost never suggest. Combined with
  skill-family-v1's 0.42 accuracy, the two-stage routing assist
  stays shadow.
