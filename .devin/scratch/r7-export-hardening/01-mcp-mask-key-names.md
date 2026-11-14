# R7-01: mcp_config masking leaks secrets under non-whitelisted key names

**Severity:** P2 (secret boundary)
**Files:** export.sh:377-405, export.ps1:151

**Defect:** `mask_value` only masks a string VALUE containing
'token'/'api_key', plus top-level keys API_KEY/TOKEN/SECRET/PASSWORD/
AUTH. A secret stored under any other key name leaks verbatim:
`env: {"GITHUB_PAT": "ghp_..."}`, `headers: {"Authorization": "Bearer x"}`,
`args` values, nested server env dicts keyed `CLIENT_ID`/`BEARER` etc.
The mask exists to make the bundle shareable; key-name misses break it
silently.

**Fix:** in the dict branch, mask when the KEY matches a secret pattern
(case-insensitive contains: token, secret, key, password, auth, bearer,
pat, credential) regardless of value; keep value-substring masking as
defense-in-depth. Mirror in export.ps1 regex list (add AUTH* variants,
BEARER, PAT, CREDENTIAL).

## Answer

Fixed + regression test in `tests/validation/test_install_export_scripts.py`.
