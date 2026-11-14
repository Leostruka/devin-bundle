# 03 -- sha256sum absent on stock macOS makes hashing silently no-op
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P1
- **File**: install.sh:50-62, export.sh:48-54

## Evidence
`file_hash()` and `dir_hash()`/`dir_hash_ext()` call `sha256sum` with stderr
discarded (`2>/dev/null`). Stock macOS ships `shasum`/`shasum -a 256`, not
`sha256sum`. With the binary missing, every call prints nothing and returns
""; `src_h == dst_h` compares empty == empty, so:

- install.sh skills loop (line 284-288) reports every skill "unchanged" and
  never installs or updates skills on macOS.
- extensions (527-530) and docs (616-619) same silent skip.
- export.sh skills (278-282) reports "unchanged" and exports nothing.

set -e does not fire because the failure happens inside `$( )` piped through
cut. Both scripts advertise macOS support in their headers.

## Recommendation
Pick a hasher at startup: `sha256sum`, else `shasum -a 256`, else hard-fail
(`err "no sha256 tool"` + exit 1) rather than silently compare empty strings.

## Tradeoffs
Hard-fail is loud but correct; alternatively fall back to `diff -rq` for
equality. Either is better than empty-string equality.

## Verification
`PATH` stripped of coreutils on macOS (or `command -v sha256sum` empty): run
`bash install.sh --dry-run` and confirm it errors instead of printing
"unchanged" for every skill.

## Answer

Both scripts detect a hasher at startup: sha256sum, then `shasum -a 256`, then `openssl dgst -sha256 -r`; absent all three they print 'ERROR: no sha256 tool found' and exit 1 instead of comparing empty strings.
