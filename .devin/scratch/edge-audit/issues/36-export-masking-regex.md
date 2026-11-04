# 36 -- Export secret masking is regex-based: org_id and token patterns can leak

- **Status**: open
- **Category**: devin-cli-limitations
- **Severity**: P2
- **File**: export.ps1:159-165

## Evidence

`export.ps1` masks secrets by regex: `org_id` literal key (line 160), a key-name pattern for token/secret/key/password/passwd/auth/bearer/credential/private/pat (163), and URL userinfo `https://user:pass@` (165). Gaps: (a) any secret stored under a key outside that vocabulary (e.g. `session`, `cookie`, `jwt`, `dsn`, `connection_string`) exports unmasked; (b) secrets in non-JSON-ish positions (multi-line strings, comments) are missed; (c) the token regex also masks innocuous keys matching the names (false positives, e.g. a `keyboard_layout` key if named unluckily); (d) `mcp_config.json` env values are masked only when the key name matches.

## Recommendation

Invert the default: for `credentials.toml` and `mcp_config.json` env blocks, mask ALL values (already done for credentials.toml) and whitelist known-safe keys; for `config.json`, mask a fixed key list (`org_id`, `user_id`, `email`) plus the existing pattern. Add a test that a synthetic secret under an unrecognized key name does not survive export.

## Tradeoffs

- Merits of current workaround: no CLI dependency, covers the known secret keys, `-NoMask` escape hatch exists for real exports.
- Demerits: denylist regex masking is structurally incomplete (new key names silently leak); fixing it by broadening the keyword list is a treadmill; whitelisting inverts to possible over-masking of non-secret config (recoverable via -NoMask or manual edit, low cost).
- Better contorno: never put secrets in exported surfaces at all; the bundle already ships `mcp_config.json.example`, so the durable fix is keeping real values out of the repo root, which the masked-export flow partially relies on anyway.

## Verification

Create a scratch config with `"dsn": "secret123"`, run `export.ps1 -DryRun`, confirm value is not masked today.
