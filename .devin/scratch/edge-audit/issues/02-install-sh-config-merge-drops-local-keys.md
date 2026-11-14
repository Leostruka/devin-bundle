# 02 -- install.sh config merge discards every local key except org_id
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P2
- **File**: install.sh:319-336

## Evidence
install.sh "merge" path (lines 325-334) does `cp "$config_src" "$config_dst"`
then re-injects only `.org_id` and `.devin.org_id` via jq. Every other local
key (theme, shell prefs, attribution, extra sections added by the user or by
newer CLI versions) is overwritten by the bundle version. install.ps1
Merge-ConfigJson (install.ps1:267-342) performs a recursive merge where local
settings win (`Merge-Hashtables $bundleHt $localHt`, line 333), preserving all
local-only keys. The two installers claim the same "merge, preserve local"
semantics but produce different results. Drift.

## Recommendation
Make the jq path a real deep-merge: `jq -s '.[0] * .[1]' bundle local` style
(jq `*` recurses for objects), or emit the merged document via a small python
recursive merge matching Merge-Hashtables semantics (bundle = base, local =
override).

## Tradeoffs
jq `*` deep-merge has the same semantics as Merge-Hashtables, so parity is
exact. The sed fallback (lines 339-360) stays lossy; worth a comment noting
the degraded mode, or keep as is.

## Verification
Local config with `"theme":"dark"` + bundle without it; run install.sh
non-force; assert `jq -r .theme config` still returns "dark".

## Answer

The jq path is now a real deep-merge: `jq -s '.[0] * .[1]' bundle local` (recursive, local wins) matching install.ps1 Merge-Hashtables semantics. All local-only keys survive, not just org_id. Verified by test_jq_deep_merge_preserves_local_keys.
