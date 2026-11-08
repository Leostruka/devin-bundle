# compact-boundary-v1 calibration run 01 (2026-11-09)

G5 evidence capture for trajectory-boundary classification
(3 labels, dict criteria). No production consumer exists yet - the
profile is contract-defined only - so this run measures raw profile
viability. Production `.devin/laya/profile.json` remains `mode: off`;
capture ran against `.devin/laya/profile.calibration.json`.

## Artifacts

- `cases.json` - maintainer-authored draft, 16 labeled cases
  (5 mid_task / 5 stage_resolved / 6 task_shifted). `snippets` carry
  a session digest (goal + action trace + pending state) in the shape
  a future compactor would emit.
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

- **Total abstention** - `__none__` on 16/16, `no_match` on all.
  raw_top_probability 0.02–0.17 (near-uniform). Trajectory
  classification requires temporal/causal reasoning over the action
  trace ("did a sub-goal just resolve? did the goal change?") -
  beyond this checkpoint's per-item semantic matching.
- **Verdict: not viable** with this checkpoint. Assist stays gated.
