# media-preset-v1 calibration run 01 (2026-11-09)

G5 evidence capture for preset selection (dynamic candidates - the
6 real grainrad presets: classic-terminal, matrix, retro-crt,
high-detail, minimal, cyberpunk; stage 2 of
`media-tools/intent.py`, reached only for stylize_image/video
intents). Production `.devin/laya/profile.json` remains `mode: off`;
capture ran against `.devin/laya/profile.calibration.json`.

## Artifacts

- `cases.json` - maintainer-authored draft, 16 labeled cases
  (12 preset picks / 4 __none__ non-preset requests).
- `manifest.frozen.json` - real worker replies frozen by
  `capture_eval.py`.
- `report.json` - `eval_decisions.py` metrics.

## Result

| metric | value |
|---|---|
| total | 16 |
| correct | 7 |
| wrong | 1 |
| abstained | 8 |
| accuracy (decided) | **0.875** |
| coverage | **0.50** |

## Failure modes observed

- **Vintage-terminal confusion** - mp-008 "1990s arcade screen" ->
  classic-terminal (gold retro-crt) at low conf 0.224. Semantically
  adjacent presets are the hard cases.
- **__none__ discipline holds** - all 4 non-preset requests
  abstained correctly.
- **Verdict: borderline viable** - second-best profile after
  media-intent-v1. The pipeline only reaches preset-pick after a
  correct intent decision, so end-to-end assist quality compounds;
  shadow evidence is consistent but thin (n=16). Same activation
  contract applies; NOT enabled.

## Held-out run (2026-11-09 - 16 fresh phrasings)

`cases.heldout.json` / `manifest.heldout.frozen.json` /
`report.heldout.json`.

| metric | value |
|---|---|
| total | 16 |
| accuracy (decided) | **1.000** (5/5) |
| coverage | **0.3125** |

Perfect precision but coverage collapsed vs run01 (0.50 -> 0.31):
poetic preset phrasings ("digital rain of falling green code
columns" for matrix, "scanlines and screen curvature" for
retro-crt) abstain while literal ones ("flat clean design",
"ultra sharp") decide correctly. Combined: ~0.92 decided acc,
~0.41 coverage - high-precision/low-recall, same shape as
knowledge-label but with real engagement. Borderline: viable only
as a conservative suggester, not a router.
