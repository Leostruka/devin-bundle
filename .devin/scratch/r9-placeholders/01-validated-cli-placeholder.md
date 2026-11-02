# R9-01: {{VALIDATED_CLI_VERSION}} never substituted in ask-bundle

**Severity:** P3 (broken placeholder in agent-facing text)
**Files:** skills/ask-bundle/SKILL.md:130, modes/orchestration-detail.md:85

**Defect:** both files contain the literal `{{VALIDATED_CLI_VERSION}}`
referencing `data/bundle-identity.json`. No install step expands it
(only {{APPDATA}}/devin is expanded, and only inside config.json).
Agents reading the skill see a placeholder instead of the version.

**Fix:** drop the literal and point at the file (the agent resolves
the value when needed): "Validated CLI: see
`data/bundle-identity.json` -> `validated_cli_version`".

## Answer

Fixed; regression asserts in tests/validation/test_install_export_scripts.py.
