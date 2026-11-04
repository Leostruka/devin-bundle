# 63 -- Partially masked credentials.toml passes the secrets gate

- **Status**: open
- **Category**: applied-rules
- **Severity**: P2
- **File**: scripts/check-push-green.py:112-132

## Evidence

`check_unmasked_secrets` blocks credentials.toml only when the literal string
`MASKED` appears nowhere in the file (line 115). A file containing one masked
entry plus real keys elsewhere passes. For mcp_config.json the regex
(line 127) detects a secret-looking value, but the subsequent
`if 'MASKED' not in content` (line 128) means a single MASKED placeholder
anywhere in the file disables blocking even when other unmasked secrets match
the regex on the same pass.

## Recommendation

Check per-entry: every value under a secret-shaped key must equal `MASKED`,
not merely coexist with one. For credentials.toml, require all values to be
masked or the file excluded from the commit entirely.

## Verification

Create credentials.toml with `a = "MASKED"` and `b = "real-secret-value"`;
feed a `git push` payload to the hook; it exits 0.
