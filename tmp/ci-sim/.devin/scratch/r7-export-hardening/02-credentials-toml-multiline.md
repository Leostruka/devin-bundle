# R7-02: credentials.toml mask leaks TOML multiline value continuations

**Severity:** P2 (secret boundary)
**Files:** export.sh:432, export.ps1 creds section

**Defect:** `sed 's/=.*/= "MASKED"/g'` masks the first line of a
multiline TOML value but leaves continuation lines raw. A stored key
written as
`key = [\n  "sk-live-abc",\n  "sk-live-def"\n]` exports the secret
strings on lines 2-3. Same for triple-quoted basic strings.

**Fix:** mask with bracket-depth tracking (awk or python): emit
`key = "MASKED"` for the line containing `=` and drop subsequent
lines until the opening `[`/`"""`/`'''` closes. Mirror in export.ps1.

## Answer

Fixed + regression test in `tests/validation/test_install_export_scripts.py`.
