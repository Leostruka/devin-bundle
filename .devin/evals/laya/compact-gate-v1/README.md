# compact-gate-v1 calibration run 01 (2026-11-09)

G5 evidence capture for context-window action selection
(continue/prune/fold/handoff/clear; live consumer
`scripts/compact-gate.py` Layer 7). State mirrors
`_digest_state`: goal = first+latest task prose, snippets = JSON
digest (tool_hist, files, errors, turns), confidence_hint =
{p, calls} pressure signal. Production `.devin/laya/profile.json`
remains `mode: off`; capture ran against
`.devin/laya/profile.calibration.json` (mode: shadow).

## Artifacts

- `cases.json` - maintainer-authored draft, 16 labeled cases across
  the pressure spectrum (p 0.22-0.95) and trajectory states.
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

- **Total abstention** - `__none__` 16/16, `no_match` everywhere.
  Same trajectory-reasoning wall as compact-boundary-v1: the action
  depends on pressure + session trajectory, not surface semantics.
- **Design note** - compact-gate.py already derives its floor
  action deterministically from pressure thresholds
  (`floor_action = continue if p < at else prune`); the laya
  suggestion is advisory on top of that. Total abstention is the
  fail-safe the design expects.
- **Verdict: not viable** with this checkpoint. Assist stays gated.
