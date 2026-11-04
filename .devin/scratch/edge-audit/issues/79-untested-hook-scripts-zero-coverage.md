# 79 -- five hook/utility scripts have zero test coverage
- **Status**: resolved
- **Category**: test-coverage
- **Severity**: P2
- **File**: scripts/architecture-gate.py, scripts/context-budget.py, scripts/memory-post-edit.py, scripts/validate-mermaid.py, scripts/mermaid-parse-check.js
## Evidence
Grepping `tests/` for each script name returns zero references:

- `architecture-gate.py` -- PreToolUse gate that blocks writes outside `.devin/` when the manifest is missing (Rule 29). No test means the path-allowlist logic (check at line 141 area) is unverified; a regression silently stops enforcing or starts blocking legitimate writes.
- `context-budget.py` -- token/context watcher, zero tests.
- `memory-post-edit.py` -- sibling of tested `memory-post-exec.py` (test_hook_memory_post_exec.py exists) but itself untested.
- `validate-mermaid.py` and `mermaid-parse-check.js` -- mermaid validation pair, zero tests.
## Recommendation
Add a `test_hook_<name>.py` per script following the existing `test_hook_stuck_detect.py`/`test_hook_gh_pr_assignee.py` pattern: feed stdin JSON, assert exit code and stdout contract. Prioritize `architecture-gate` (security-adjacent gate) and `context-budget` (fires every prompt).
## Verification
`grep -rn "architecture-gate\|context-budget\|memory-post-edit\|validate-mermaid\|mermaid-parse-check" tests/ --include="*.py"` returns no `.py` matches today.

## Answer
Added tests/test_hook_architecture_gate_edge.py, test_hook_context_budget_edge.py, test_hook_memory_post_edit_edge.py, test_hook_validate_mermaid_edge.py, test_hook_mermaid_parse_check_edge.py covering stdin contracts, exit codes, gating, fail-open paths, and block decisions. Hook scripts themselves untouched.

Status: resolved
