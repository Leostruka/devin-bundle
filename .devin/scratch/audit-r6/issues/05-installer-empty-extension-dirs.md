# 05 -- install.sh copies empty extension dirs and reports installed

- **Status**: resolved
- **Severity**: P3
- **File**: `install.sh` extensions loop (~line 500)

## Evidence

`for ext_dir in "$ext_src"/*/` iterates every directory including
empty ones (`extensions/spline-operator/` is currently an empty local
artifact). The installer creates the empty dir under
`$DEVIN_HOME/extensions/` and prints `extensions/spline-operator
installed` -- a false success report and dead weight in the live
config. Git cannot track empty dirs, so the fix must live in the
installer, not the repo tree.

## Fix

Skip dirs with no files: `find "$ext_dir" -mindepth 1 -type f -print
-quit` empty -> `skip` line instead of install.

## Verification

`install.sh --dry-run` reports `extensions/spline-operator` as
skipped, not installed.

## Answer

Fixed. The extensions loop now checks `find "$ext_dir" -mindepth 1
-type f -print -quit` and reports `extensions/$name is empty` via the
skip() channel instead of installing an empty dir. Verified via
`install.sh --dry-run`: spline-operator reported empty/skipped.
Static regression in test_install_export_scripts.py.
