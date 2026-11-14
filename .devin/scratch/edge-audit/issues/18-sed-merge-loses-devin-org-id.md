# 18 -- install.sh sed fallback merge loses devin.org_id
- **Status**: resolved
- **Category**: user-experience
- **Severity**: P2
- **File**: install.sh:339-361

## Evidence
When `jq` is absent, the config.json merge falls back to sed (lines 339-361). It extracts only the first `org_id` match (`head -1`, line 343), then rewrites every `"org_id": "..."` occurrence to `"MASKED"` (lines 347-349), then restores only `local_org_id`. The nested `.devin.org_id` is captured in the jq path (`local_devin_org_id`, line 324) but never in the sed path, so a real local `devin.org_id` is permanently replaced by `MASKED` whenever the user lacks `jq`.

This is silent data loss of a config value the merge explicitly promises to preserve ("preserve org_id" in the step header, line 308).

## Recommendation
Either require jq for the merge (warn and skip config.json with a clear message when it is missing), or extend the sed fallback to handle `devin.org_id` the same way the jq path does. The safer option is to skip the merge and tell the user to install jq, since sed on JSON is fragile in general.

## Tradeoffs
Merits of skipping: no silent corruption, explicit failure. Demerits: users without jq get no config at all until they install it; on minimal WSL/Git-Bash setups jq is commonly absent.

## Verification
Create a local config with `"devin": {"org_id": "real-id"}`, run the sed path (temporarily hide jq), and observe `"org_id": "MASKED"` inside the `devin` block after install.

## Answer

The lossy sed fallback was removed: without jq the merge is skipped loudly ('install jq, or re-run with --force') and recorded, so devin.org_id can no longer be silently replaced by MASKED.
