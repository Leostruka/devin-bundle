# Contract C4: JPEG XL codec in media-tools

- Role: `implementer`
- Lane: worktree `.worktrees/jxl`, branch `feat/media-tools-jxl`
- Objective: JXL decode/encode/identify in `extensions/media-tools` via
  `cjxl`/`djxl` (libjxl), bootstrapped explicitly like `extensions/asr`.
- Output:
  - `extensions/media-tools/jxl.py` (or equivalent module entry): `identify`,
    `decode` (jxl->png), `encode` (png->jxl, optional `-q`), typed JSON output.
  - `extensions/media-tools/jxl_bootstrap.py`: explicit fetch of prebuilt
    libjxl Windows binaries into `_cache/` (never silent at call time —
    report `missing` + hint).
- Boundaries: no Pillow plugin dep; no ROI encoding yet; keep existing
  media-tools API untouched.
- VFs: round-trip fixture png->jxl->png; `pytest -q tests/` media-tools tests
  green; audit 0 errors.
- Report: `.devin/handoffs/C4-media-tools-jxl-out.md`.
