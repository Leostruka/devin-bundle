# audit-r4 -- issue map

Fourth audit round (after general + r1 + r2 + r3). Scope: files never
deep-audited -- remotion-render plan_check, asr bootstrap, system-control
bench, scrape-tools, laya_cli, skill-picker, consolidated-hook entry
points, manifest/script registration.

| # | File | Defect | Severity | Status |
|---|------|--------|----------|--------|
| 01 | `extensions/remotion-render/plan_check.py` | untyped errors (missing file, bad JSON, non-dict plan, malformed beats) | P2 | resolved |
| 02 | `extensions/asr/bootstrap.py` | zero error handling + unvalidated `extractall` + `--model` path traversal | P2 | resolved |
| 03 | `extensions/system-control/sc_bench.py` | manual arg parse crashes on non-int | P3 | resolved |

## Scanned, clean

- `extensions/scrape-tools/{scrape,parse,dom_elements,st_common}`:
  typed `fail()`/`read_error:`/`input_too_large` contracts, browser tier
  gated behind explicit install consent.
- `scripts/skill-picker.py`: bounded manifest read (2MB), slug-only
  skill names (injection-safe), cap absolute.
- `extensions/laya-tools/laya_cli.py`: subprocess timeout honored.
- `extensions/laya-tools/layad.py`: atomic daemon-info write.
- `scripts/context-pressure.py`, `user-prompt.py`, `session-start.py`,
  `stop-guard.py`, `memory-stop.py`: typed/fail-open contract held.
- `manifest.json` scripts array: all 33 registered, none missing.
- `extensions/computer-use/*`, `extensions/*/*.py` AST sweep for
  unguarded `json.load`: only the two confirmed files hit.

## Notes (not defects)

- `_hookrun`/hook stdin is uncapped JSON -- payload size is controlled
  by the Devin runtime; no evidence of abuse. Parked.
- `stuck-detect.py` concurrent-exec race can drop one history event;
  streak catches up next call. Acceptable for an advisory.
