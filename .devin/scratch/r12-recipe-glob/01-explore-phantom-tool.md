# R12-01: explore recipe lists phantom tool `glob`

**Severity:** P3 (scoring skew)
**File:** data/recipes.json

**Defect:** `recipes.explore.tools` = `["glob", "find_file_by_name",
"read", "grep"]`. `glob` is not a Devin CLI tool (the glob-pattern
matcher is `find_file_by_name`, already listed). Consumer
`scripts/context-pressure.py:score_recipe` computes
`tool_score = |available ∩ needed| / |needed|` -- `glob` can never be
in `available`, so explore's tool_score caps at 0.75 instead of 1.0.

**Fix:** drop `"glob"` from the tools list.

## Answer

Removed `glob` from explore.tools; regression assert validates every
recipe tool against the CLI tool set.
