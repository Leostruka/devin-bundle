# r20-dep-drift-01: declared-unused playwright + missing ppisp-prep requirements

## Defects

1. `extensions/craft-bridge/requirements-ui.txt` declared `playwright==1.55.0` — added in the EGM rollout (#253) but no code path ever imports or drives it (verified via `git log -S playwright -- extensions/craft-bridge/` = requirements file only, and zero import references repo-wide). Orphaned dependency: installs a heavy browser stack for nothing when consumed.
2. `extensions/ppisp-prep/` had no requirements file while `photo_qc.py` hard-imports `numpy` at top level and uses PIL in `_load_rgb`. Siblings (image-forensics, media-tools) declare theirs; ppisp-prep could not be provisioned from its own metadata. `torch` import in `ppisp_runner.doctor()` is a lazy capability probe, correctly left undeclared.

## Fixes

- requirements-ui.txt: playwright line removed
- image-forensics/requirements.txt: `opencv-python-headless` and `piexif` removed (declared as "optional, stronger when present" but no code path ever imports them; PRNU uses numpy+PIL, metadata uses PIL getexif)
- ppisp-prep/requirements.txt created: numpy>=1.26, pillow>=10.0
- New `test_extension_declared_deps_used` regression: every requirement declared by an extension must appear in that extension's own Python imports; PIP_TO_IMPORT map covers pillow->pil, opencv->cv2, pywinpty->winpty, winrt-*->winrt

## Verified

New test caught all three orphans on first run; 30/30 validation tests pass after fixes; photo_qc imports are the only hard third-party imports in ppisp-prep.
