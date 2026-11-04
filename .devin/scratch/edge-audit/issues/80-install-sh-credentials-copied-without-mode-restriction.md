# 80 -- install.sh copies credentials.toml and mcp_config.json with default permissions
- **Status**: open
- **Category**: security
- **Severity**: P2
- **File**: install.sh:500, 506
## Evidence
`cp "$creds_src" "$creds_dst"` (lines 500, 506) installs `credentials.toml` into `$DEVIN_HOME` preserving a 0644-style mode (cp applies source mode minus umask; no `chmod` follows anywhere in install.sh -- `grep -n chmod install.sh` is empty). When `--restore-secrets` has populated real API keys (`windsurf_api_key`, `devin_api_url`), the file lands world-readable on multi-user POSIX systems. Same pattern applies to the `mcp_config.json` copy path which can carry tokens.
## Recommendation
After installing `credentials.toml` and `mcp_config.json`, run `chmod 600` (respecting `$DRY_RUN`). Optionally set `umask 077` for the credentials/config install block.
## Verification
On Linux/WSL: run `install.sh --restore-secrets`, then `stat -c %a "$DEVIN_HOME/credentials.toml"`; expect 600, observe source mode (typically 644).
