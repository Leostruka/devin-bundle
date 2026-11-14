# r17-phantom-tool-01: `glob` phantom in skill allowed-tools frontmatter

## Problem

`skills/observability-quality/SKILL.md` declared `allowed-tools: [read, grep, glob, edit, write, exec]` — `glob` is not a CLI tool (same phantom class as R12's `recipes.json` defect). No check covered skill frontmatter tool names.

## Fix

- `glob` -> `find_file_by_name` (the actual file matcher tool)
- New `test_skill_allowed_tools_exist` regression: every `allowed-tools` entry across all SKILL.md files validated against the canonical tool set (shared `VALID_TOOLS` constant with the R12 recipe test)

## Verified

27 allowed-tools values scanned; exactly 1 violation (this one).
