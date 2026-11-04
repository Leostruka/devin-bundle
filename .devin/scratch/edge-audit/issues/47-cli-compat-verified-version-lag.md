# 47 -- DEVIN-CLI-COMPATIBILITY verified versions lag validated CLI

- **Status**: resolved
- **Category**: documentation
- **Severity**: P3
- **File**: .devin/docs/DEVIN-CLI-COMPATIBILITY.md:9,44

## Evidence
Section headers read "verified 2026-09-15, CLI 3000.10.27" and "verified
2026-09-22, CLI 3000.11.1", while `data/bundle-identity.json:8` declares
`validated_cli_version: 3000.11.234`. TOOLS-MAP already documents fields
introduced in 3000.11.205/3000.11.234 (`fail_closed`, `stop`,
`updatedInput`, `updatedToolOutput`, `session_id`, `prompt_id`), but the
compatibility doc that is supposed to track adoption decisions has no
3000.11.9x+ section beyond a passing note. There is no stated cadence or
owner for re-verifying the doc against the validated version.

## Recommendation
Add a 3000.11.x-later section covering 3000.11.92 through 3000.11.234
adoptions, and stamp each section with the identity version it was
checked against. Alternatively record per-decision `verified_at` fields.

## Verification
grep every version literal in `data/bundle-identity.json` and
`bundle-models.json` against DEVIN-CLI-COMPATIBILITY; each validated
minor must appear in a section header.

## Answer

Added a `## Verification cadence` section to DEVIN-CLI-COMPATIBILITY.md: doc tracks `validated_cli_version`, every section stamped with the checked version, new section required per validated bump, owner = whoever bumps bundle-identity.json. Sections already cover 3000.11.92 through 3000.11.234.
