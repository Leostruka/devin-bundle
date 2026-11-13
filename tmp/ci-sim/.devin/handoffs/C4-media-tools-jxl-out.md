# C4 media-tools JPEG XL - handoff

## Status

DONE

## What landed

Branch `feat/media-tools-jxl` (worktree `.worktrees/jxl`), commit `d2566da`
`feat(media-tools): JPEG XL codec via cjxl/djxl`.

- `extensions/media-tools/jxl.py` - CLI wrapper over `cjxl`/`djxl`/`jxlinfo`,
  stdlib + subprocess only. Actions: `identify` (dims, colorspace, alpha,
  frames; jxlinfo preferred, djxl+PNG-IHDR fallback), `decode` (jxl->png),
  `encode` (png->jxl, `-q` quality 0-100, `-e` effort 1-9). Typed JSON
  envelope; missing binaries -> `{"ok": false, "status": "missing",
  "hint": "run extensions/media-tools/jxl_bootstrap.py"}`. Tool resolution:
  `_cache/jxl-paths.json` -> `_cache/` scan -> PATH. No network at call time.
- `extensions/media-tools/jxl_bootstrap.py` - explicit fetch of pinned
  libjxl v0.11.2 release zips (Windows x64/x86, Linux x86_64), sha256
  verified, zip-slip guarded member extraction, writes
  `_cache/jxl-paths.json`. Same convention as `extensions/asr/bootstrap.py`.
- `extensions/media-tools/.gitignore` - added `_cache/` (kept existing
  `custom_presets.json` entry).
- `tests/test_jxl.py` - missing-binary envelope, typed input/params errors,
  and a real round-trip: stdlib-generated PNG -> encode(q=100) -> decode ->
  pixel equivalence within tolerance (max channel diff <= 8). Skips when
  binaries absent.

## Verification

- `python jxl_bootstrap.py` -> `{"ok": true, ...}`; zip sha256 verified,
  binaries extracted to `_cache/bin/`.
- `python -m pytest tests/test_jxl.py -q` -> 4 passed (round-trip ran with
  real cjxl/djxl on Windows x64).
- `python audit.py` -> 0 errors, 4 warnings (pre-existing
  `skills/* live != bundle` drift, unrelated).
- `python -m pytest -q tests/` -> 2137 passed, 5 skipped; 1 failure
  (`test_stop_guard_passes_clean`) caused by em-dashes in this report's
  first draft; prose rewritten, re-run of that test plus test_jxl.py is
  green (5 passed).

## Boundaries respected

No Pillow plugin, no ROI encoding, no public-API changes to existing
media-tools modules, no AI signature, no push. Only `extensions/media-tools/`
and `tests/test_jxl.py` touched.
