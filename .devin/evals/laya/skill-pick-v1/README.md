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

## Result (CORRECTED 2026-11-09 - see UTF-8 bug below)

| metric | value |
|---|---|
| total | 30 |
| correct | 4 |
| wrong | 0 |
| abstained | 26 |
| accuracy (decided) | **1.000** |
| coverage | **0.133** |

## UTF-8 stdio bug - original capture was corrupted

The run-01 manifest recorded 25/30 `engine_error:TypeError` (not
the 4 transient errors first reported - the frozen evidence shows
25). Root cause found 2026-11-09: the worker's `sys.stdin` used
the Windows locale encoding (cp1252) while clients write UTF-8.
Skill-purpose texts contain em-dashes; UTF-8 bytes decoded as
cp1252 + surrogateescape produced lone surrogates (`\udc9d`)
that the Rust tokenizer rejects with TypeError. Requests with
pure-ASCII candidates (sp-026..030) were unaffected - hence the
clean 26-boundary. Fix: `decision_contract.pin_stdio_utf8()`
called from `laya_worker.main()` and `laya_cli.main()`.

Post-fix recapture (`manifest.utf8.frozen.json` /
`report.utf8.json`):

| metric | value |
|---|---|
| total | 30 |
| accuracy (decided) | **0.882** (15/17) |
| coverage | **0.567** |

The "extreme abstention" verdict was an artifact of the encoding
bug - the engine engages fine on 8-candidate skill shortlists.
Remaining failure: sp-022 "control the local screen" ->
system-control at p=0.935 (gold computer-use) - a high-confidence
wrong between genuinely overlapping skills; sp-012 wrong at
p=0.337 (gate-rejectable). Verdict upgraded: borderline viable,
second-tier behind media-intent-v1; assist still gated.

## Failure modes observed

- **Extreme abstention on 8-candidate sets** - decided only 4/30
  (all assistance/knowledge families with shorter purposes);
  development/investigation/operations/visual shortlists produced
  `no_match` nearly always. Long purpose texts as criteria do not
  engage the matcher.
- **engine_error:TypeError x25** - originally misreported as 4
  transient errors; actually the stdio encoding bug above. Fixed
  by `pin_stdio_utf8()`; see corrected results.
- **Verdict (superseded)** - the 13% coverage was encoding-bug
  artifact; corrected run shows 0.882/0.567. Still shadow: one
  high-confidence wrong on overlapping skills (sp-022) plus the
  standard activation checklist applies.
