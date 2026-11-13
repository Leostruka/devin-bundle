# R9-02: bundle-identity.json ships unexpanded {{BUNDLE_*}} placeholders

**Severity:** P3 (broken data for consumers)
**File:** data/bundle-identity.json

**Defect:** `bundle_name`, `owner`, `repo`, `source_url`,
`license_holder`, `license_year` are template placeholders
(`{{BUNDLE_NAME}}` etc.). Consumers that read them -- e.g.
skill-discovery building `gh search repos` URLs -- produce broken
output. `validated_cli_version` is the only real value.

**Fix:** fill real values for this bundle
(devin-bundle / Leostruka / devin-bundle / license year).

## Answer

Fixed; regression asserts in tests/validation/test_install_export_scripts.py.
