# 04 -- strip_bom uses GNU sed -i syntax, fails on macOS (set -e aborts)
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P2
- **File**: install.sh:116, export.sh:124

## Evidence
`strip_bom` runs `sed -i '1s/^\xEF\xBB\xBF//' "$file"`. BSD sed (macOS)
requires a backup suffix argument: `sed -i '' ...`. On macOS this errors with
"invalid command code" and, under `set -euo pipefail`, aborts the whole
install/export mid-run (agent files already copied, rest skipped). The same
scripts already handle the Darwin split correctly in `convert_to_lf`
(export.sh:62-66) and the config-merge sed (install.sh:346-349), so this is
an inconsistent missed case, not a policy.

## Recommendation
Reuse the existing Darwin branch:
`if [[ "$(uname)" == "Darwin" ]]; then sed -i '' '1s/^\xEF\xBB\xBF//' "$file"; else sed -i '1s/^\xEF\xBB\xBF//' "$file"; fi`
Or drop sed and strip via `tail -c +4 "$file" > tmp && mv` (also fixes the
`\xEF` escapes, which BSD sed does not interpret anyway).

## Tradeoffs
None material; `tail -c +4` is simpler and portable.

## Verification
On macOS: create agent .md with EF BB BF prefix, run export.sh, confirm it
completes and BOM is stripped.

## Answer

strip_bom no longer uses `sed -i`; it strips via `tail -c +4` to a temp file + mv, which is portable across GNU and BSD (and sidesteps BSD sed not interpreting ï escapes).
