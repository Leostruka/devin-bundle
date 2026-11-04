# 06 -- export.sh masks only org_id; ps1 masks all secret-named keys and credentialed URLs
- **Status**: open
- **Category**: code-optimization
- **Severity**: P2
- **File**: export.sh:307-319 vs export.ps1:156-167

## Evidence
export.sh masked config path (python inline, lines 307-319) sets only
`data['org_id']` and `data['devin']['org_id']` to MASKED. export.ps1
Mask-JsonSecrets additionally masks every JSON key whose name matches
`token|secret|key|password|passwd|auth|bearer|credential|private|pat`
(line 163) and `https://user:pass@` URLs (line 165). A config.json carrying
e.g. `"github_token": "ghp_..."` under any section is exported raw by
export.sh but masked by export.ps1. Same for nested org_id beyond `.devin`
(the ps1 regex `("org_id"\s*:\s*")[^"]+` matches anywhere in the document).

## Recommendation
Reuse the same masking routine used for mcp_config (export.sh:405-435, the
`mask_value`/`SECRET_KEY` inline python) for config.json, then set hooks={}
and org_id explicitly. One masking implementation for both files also kills
the drift class.

## Tradeoffs
Recursive key-name masking can over-mask innocuous keys containing "key"
(e.g. "keybindings"); ps1 already accepts that tradeoff, so parity argues
for applying it here too.

## Verification
Put `"api_token":"secret123"` in a test config.json, run
`export.sh` masked path, grep exported config.json for "secret123" (expect
absent) and for `"MASKED"`.
