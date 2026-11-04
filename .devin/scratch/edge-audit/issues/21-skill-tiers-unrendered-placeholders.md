# 21 -- SKILL-TIERS.md ships unrendered {{BUNDLE_*_MODEL}} placeholders
- **Status**: resolved
- **Category**: organization
- **Severity**: P3
- **File**: .devin/docs/SKILL-TIERS.md (model table, ~lines 12-18)

## Evidence
The tier table reads `| \`{{BUNDLE_MEDIUM_MODEL}}\` (\`swe-2-medium\`) | Medium | ... |` and similar for `{{BUNDLE_DEFAULT_MODEL}}` and `{{BUNDLE_MAX_MODEL}}`. These placeholders are never substituted: install.ps1 copies `.devin/docs` verbatim into `%APPDATA%\devin\docs` via `Install-SkillDir`/`Copy-FilteredDir` (lines 600-618) with no token expansion, and install.sh does the same via `cp -r` (lines 609-630). The only placeholder expansion anywhere is `{{APPDATA}}`/`{{APPDATA}}/devin` inside config.json.

The doc does mention the env vars `BUNDLE_MAX_MODEL` / `BUNDLE_MEDIUM_MODEL` and `data/bundle-models.json`, so the intent appears to be "literal env var name", but the `{{...}}` syntax reads as an unrendered template to any agent or user consuming it, and `{{BUNDLE_DEFAULT_MODEL}}` has no corresponding env var documented in the same paragraph.

## Recommendation
Either replace `{{BUNDLE_*_MODEL}}` with the resolved values from `data/bundle-models.json` at export/install time, or rewrite the table to say `env BUNDLE_MEDIUM_MODEL (default swe-2-medium)` so nothing looks like a template token.

## Verification
`grep -n "{{BUNDLE" .devin/docs/SKILL-TIERS.md`; `grep -rn "BUNDLE_" install.ps1 install.sh export.ps1 export.sh scripts/render-user-hooks.py` shows no substitution step for these tokens.

## Answer

Replaced all `{{BUNDLE_*_MODEL}}` placeholders with literal env-var names plus defaults (`BUNDLE_MEDIUM_MODEL` (default `swe-2-medium`) etc.) in SKILL-TIERS.md; same cleanup applied to TOOLS-MAP.md, MODEL-GUIDE.md, DEVIN-CLI-COMPATIBILITY.md (`{{VALIDATED_CLI_VERSION}}` -> 3000.11.234). `grep -n '{{BUNDLE' .devin/docs/SKILL-TIERS.md` returns 0.
