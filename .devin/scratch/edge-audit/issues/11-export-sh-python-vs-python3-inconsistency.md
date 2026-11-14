# 11 -- export.sh validation calls `python` while masking required `python3`
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P3
- **File**: export.sh:552, 562

## Evidence
Pre-push validation runs `( cd "$BUNDLE_DIR" && python audit.py )` and
`python -m pytest -q`. Everywhere else the script requires `python3`
(masking at 304, 402, 463) or falls back through `command -v python3 ...
python` (install.sh:93-101). On a system with only `python3` (common on
modern Linux/macOS), masking succeeds but the validation block fails with
command-not-found, `validation_failed=1`, and the push aborts -- a false
blocking failure at the final step.

## Recommendation
Resolve one interpreter at the top: `PY=$(command -v python3 || command -v python)`
and use `"$PY"` for audit.py, pytest, and all inline `-c` blocks. export.ps1
has the same latent issue calling bare `python` (Test-PythonSyntax line 215,
render hook line 531) but that is Windows where `python` is the canonical
name; note only.

## Tradeoffs
None.

## Verification
On a host where `python` is absent and `python3` present: `export.sh --push`
reaches and passes the audit/pytest steps instead of aborting.

## Answer

One interpreter is resolved once (PY=python3 else python); every call -- masking, json.tool, ast syntax check, audit.py, pytest, credentials masking -- goes through the `python()` wrapper, so python3-only hosts no longer fail at the audit/pytest steps.
