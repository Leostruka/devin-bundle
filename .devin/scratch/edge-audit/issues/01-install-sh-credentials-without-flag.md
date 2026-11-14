# 01 -- install.sh installs unmasked credentials.toml without --restore-secrets
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P1
- **File**: install.sh:485-508

## Evidence
install.sh lines 485-508: when `credentials.toml` exists and does not contain
MASKED, the script goes straight to the normal copy path (line 506
`cp "$creds_src" "$creds_dst"`). `RESTORE_SECRETS` is never consulted on the
unmasked branch. install.ps1 lines 584-593 gates the same install behind
`-RestoreSecrets` and refuses otherwise. Result: `./install.sh` (no flags)
silently plants real API keys into `$DEVIN_HOME/credentials.toml`, while the
.ps1 refuses. Behavioral drift plus secrets materialized without opt-in.
Also the usage text (line 25) promises `--restore-secrets` restores masked
values, but the mcp_config branch (line 459) prints "not implemented yet".

## Recommendation
Mirror the ps1 gate: `if [[ $RESTORE_SECRETS -eq 0 ]]; then skip ...; fi`
before the copy block; fix the help text to match actual behavior.

## Tradeoffs
Adds one flag check; changes behavior for anyone relying on the silent copy
(unlikely and unsafe to rely on).

## Verification
`bash install.sh --dry-run` with an unmasked credentials.toml in the bundle:
expect "use --restore-secrets" skip, not "credentials.toml installed".

## Answer

Unmasked credentials.toml is now gated behind --restore-secrets (`elif [[ $RESTORE_SECRETS -eq 0 ]]` warns and records a skip, no copy). Masked-file messaging and the usage text were corrected (issue 19). Verified by test_unmasked_credentials_skipped_without_flag and test_unmasked_credentials_install_with_flag_mode_600 in tests/test_install_sh_edge_audit.py.
