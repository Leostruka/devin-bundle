# ui-target-v1 calibration run 01 (2026-11-09)

G5 evidence capture for UI element targeting (dynamic candidates -
observed elements as id/role/name/scope; live consumer
`cu_decision.py`/`cu_dom_picker.py` in the computer-use lane).
Production `.devin/laya/profile.json` remains `mode: off`; capture
ran against `.devin/laya/profile.calibration.json` (mode: shadow).

## Artifacts

- `cases.json` - maintainer-authored draft, 20 labeled cases
  (14 element picks / 6 __none__), realistic dialogs, forms, media
  players, settings pages.
- `manifest.frozen.json` - real worker replies frozen by
  `capture_eval.py`.
- `report.json` - `eval_decisions.py` metrics.

## Result

| metric | value |
|---|---|
| total | 20 |
| correct | 10 |
| wrong | 4 |
| abstained | 6 |
| accuracy (decided) | **0.714** |
| coverage | **0.70** |

## Failure modes observed

- **Deadline misses** - 4/20 hit `deadline_exceeded` (20%), the
  highest rate of any profile; dynamic candidate sets cost more
  engine time at the 1000ms budget.
- **Dangerous __none__ commits** - the disqualifying direction for
  a click gate: ut-004 "export to PDF" -> Save, ut-010 coordinate
  goal -> OK button, ut-014 "second result" -> Result Two (index
  reasoning unsupported), ut-020 "logo home" -> Menu. When no
  element fits, the model still commits instead of abstaining.
- **Verdict: not viable for assist.** A wrong element suggestion in
  computer-use acts on the wrong target; abstention is the only
  safe failure and this profile does not abstain reliably.
