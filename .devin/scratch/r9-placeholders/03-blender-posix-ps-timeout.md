# R9-03: blender-operator POSIX `ps` subprocess missing timeout

**Severity:** P3 (parity)
**File:** extensions/blender-operator/wrapper.py:~130

**Defect:** the POSIX branch of `_find_pids` runs
`subprocess.run(["ps", ...])` with no `timeout=`; the powershell
branch uses timeout=15. `ps` realistically cannot hang, but the
asymmetry is an oversight.

**Fix:** `timeout=15` on the POSIX `ps` call.

## Answer

Fixed; regression asserts in tests/validation/test_install_export_scripts.py.
