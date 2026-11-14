# R7-04: export --commit stages unrelated dirty files via git add -A

**Severity:** P3 (commit hygiene)
**Files:** export.sh:528, export.ps1 commit step

**Defect:** `--commit` runs `git add -A`, sweeping every unrelated
uncommitted change in the working tree into the generated
"export: refresh devin bundle" commit.

**Fix:** add only the exported paths (AGENTS.md agents skills
config.json scripts data mcp_config.json credentials.toml export.ps1
if it was rewritten) and evaluate `git status --porcelain` on those
paths alone.

## Answer

Fixed + regression test in `tests/validation/test_install_export_scripts.py`.
