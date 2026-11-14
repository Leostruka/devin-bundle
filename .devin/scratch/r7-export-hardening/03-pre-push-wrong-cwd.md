# R7-03: pre-push audit.py + pytest run in caller cwd, not bundle root

**Severity:** P2 (gate silently broken; Rule 5)
**Files:** export.sh:497-505, export.ps1:518-531

**Defect:** `python "$BUNDLE_DIR/audit.py"` runs with cwd = wherever the
user invoked export.sh. audit.py walks `.` and reads `manifest.json`,
`AGENTS.md`, `config.json` relative to cwd -- so run from outside the
repo it audits the wrong tree or crashes on missing files. The "audit
passed" line can certify nothing. pytest has the same cwd/rootdir
problem.

**Fix:** run both inside a subshell `cd "$BUNDLE_DIR"` (bash) /
Push-Location (ps1).

## Answer

Fixed + regression test in `tests/validation/test_install_export_scripts.py`.
