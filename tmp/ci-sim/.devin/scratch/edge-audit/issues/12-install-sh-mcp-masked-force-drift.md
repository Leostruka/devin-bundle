# 12 -- masked mcp_config.json: ps1 -Force installs it, sh never does
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P3
- **File**: install.sh:455-460 vs install.ps1:566-574

## Evidence
install.sh: if `contains_masked "$mcp_src"` the file is skipped outright --
no code path installs it, not even `--force` (line 457 warns and moves on).
install.ps1: `-Force` installs the masked file deliberately
("Install the file structure anyway? Use -Force", lines 569-571), which is
useful to get server entries/URLs in place and fill tokens manually. Same
flag, different outcome across platforms: drift in a user-visible install
option.

## Recommendation
Pick one semantic. The ps1 behavior is more useful and still safe (values
are MASKED, not real secrets): in install.sh, allow `--force` to install the
masked file with a clear warning that tokens must be filled manually.

## Tradeoffs
Installing masked mcp_config can break a working existing file if the user
runs --force blindly; the ps1 already accepts that. Alternatively drop the
ps1 -Force path to match sh's always-skip.

## Verification
Masked mcp_config.json in bundle + `install.sh --force`: file installed
with MASKED placeholders (matching ps1) or explicitly skipped by design --
assert whichever semantic is chosen in both installers.

## Answer

--force now installs the masked mcp_config.json deliberately (with a 'fill tokens manually' warning and chmod 600), matching install.ps1 -Force semantics. Verified by test_masked_mcp_skipped_then_force_installed.
