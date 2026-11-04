# 19 -- --restore-secrets flag promises more than it does
- **Status**: open
- **Category**: user-experience
- **Severity**: P3
- **File**: install.sh:25, 451-479, 487-491

## Evidence
`usage()` documents `--restore-secrets` as "Restore masked values in credentials.toml and mcp_config.json" (line 25). In practice:

- For `mcp_config.json`, when the file is masked the flag only prints `Use --restore-secrets to restore from local file (not implemented yet)` (line 459). Nothing is restored.
- For `credentials.toml`, when masked the flag only prints `cannot restore automatically` / `manually restore credentials.toml from your backup` (lines 488-489). Nothing is restored.
- When files are unmasked, mcp_config.json installs even without the flag, and credentials.toml installs without the flag either (install.sh:493-508; tracked separately as issue 01 in this audit), so the flag never changes behavior except adding warnings.

install.ps1 also cannot unmask values, but its `-RestoreSecrets` switch at least controls whether the file is installed at all, so the flag is meaningful there. The missing `--force` install path for masked mcp_config.json is tracked separately (issue 12).

## Recommendation
Reword `usage()` to describe actual behavior (e.g. "opt in to installing credentials.toml when it contains real values"), and either implement masked-value restoration or remove the flag's claim to do so.

## Verification
Run `./install.sh --restore-secrets --dry-run` with masked files: the only difference vs a plain run is extra warning lines; no restore occurs.
