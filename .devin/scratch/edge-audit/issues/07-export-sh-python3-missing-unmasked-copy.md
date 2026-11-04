# 07 -- export.sh without python3 exports secrets unmasked or aborts mid-run
- **Status**: open
- **Category**: code-optimization
- **Severity**: P1
- **File**: export.sh:304-329, 402-442, 463-485

## Evidence
Two failure modes when `python3` is absent (possible on Git Bash / minimal
POSIX where only `python` exists):

1. config.json: lines 325-328 warn then `cp "$config_src" "$config_dst"` --
   UNMASKED, including org_id and any embedded secrets. Same pattern for
   mcp_config.json lines 439-442. The export reports "exported (unmasked)"
   and continues; the bundle then holds real secrets with no hard stop,
   and only a later manual `audit.py` run would flag it.
2. credentials.toml: line 463 calls `python3 -c` unconditionally under
   `set -euo pipefail`; command-not-found exits 127 and kills the script
   after config/mcp were already written (half-applied export).

export.ps1 has no python dependency for masking (pure regex), so this drift
only exists on the .sh side.

## Recommendation
- Fail closed: if no python interpreter is found, `err` + `exit 1` on the
  masked path instead of copying unmasked.
- Accept `python` as fallback (`command -v python3 || command -v python`),
  matching expand_devin_home_in_config in install.sh:93-101.

## Tradeoffs
Hard fail blocks export on bare systems; that is the correct failure for a
secrets-bearing operation.

## Verification
`PATH` without python3: `export.sh` must exit nonzero with an error, and the
bundle config.json must not contain the source org_id.
