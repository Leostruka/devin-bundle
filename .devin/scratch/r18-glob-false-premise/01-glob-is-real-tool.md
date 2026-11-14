# r18-glob-false-premise-01: `glob` is a real CLI tool; R17 fix reverted

## Problem

R12 and R17 treated `glob` as a phantom tool name based on the session toolset, which lacks it. Verification against the bundle's own canonical sources proves otherwise: `scripts/validate-tool-args.py` has a `check_glob` checker and `.devin/docs/TOOLS-MAP.md` documents `glob` as a distinct Search tool (path glob matching, vs `find_file_by_name` name matching). The session toolset is mode-dependent and not canonical.

## Corrections

- `observability-quality` allowed-tools restored: `glob` (kept `find_file_by_name` too; both real)
- `VALID_TOOLS` in the validation test expanded to the canonical 28-tool set mirroring the TOOLS-MAP table (adds glob, apply_patch, exit_plan_mode, get_output, write_to_process, kill_shell)
- `test_skill_allowed_tools_exist` extended: YAML-list frontmatter form and `agents/` + `.devin/agents/` profiles now covered
- `data/recipes.json` R12 removal kept: defensible on different grounds (a recipe should not demand a tool absent from some session toolsets; `find_file_by_name` covers file matching)

## Note

Agent profiles legitimately declare `glob`; subagent toolsets differ from the parent session's.
