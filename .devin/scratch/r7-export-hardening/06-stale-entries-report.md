# R7-06: export never reports bundle entries absent from live config

**Severity:** P3 (silent drift)
**Files:** export.sh skills/scripts/data/agents loops, export.ps1 same

**Defect:** export copies live -> bundle one-way. A skill/script/agent
present in the bundle but missing from DEVIN_HOME stays forever with
no signal -- deleted-upstream items silently persist in the repo.
Auto-deleting is wrong both ways (bundle may hold not-yet-installed
work), but a report is free signal.

**Fix:** after each copy loop, list dst entries absent from src as
"bundle-only (kept -- remove manually if unintended)" warnings.

## Answer

Fixed + regression test in `tests/validation/test_install_export_scripts.py`.
