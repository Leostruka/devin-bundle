---
name: debug-ci-failures
description: Use when CI is failing and the cause needs to be found across builds, jobs, or environments.
---
# Debug CI Failures

Systematically diagnose and resolve CI failures. CI-agnostic — works with GitHub Actions, CircleCI, GitLab CI, Jenkins, or any CI system.

## Decision logic: which CI system

| CI System | How to access | Tools |
|---|---|---|
| GitHub Actions | `gh run list`, `gh run view`, `gh api` | `gh` CLI (preferred) |
| CircleCI | CircleCI MCP server (if configured) | `mcp__circleci-mcp-server__*` |
| GitLab CI | `glab ci list`, `glab ci view` | `glab` CLI |
| Jenkins | `jenkins-cli` or HTTP API | `jenkins` CLI |
| Other / unknown | Read CI config + parse logs manually | `webfetch`, `curl`, log files |

If no CI CLI or MCP is available, ask the user to provide the failure logs or a URL to the failed pipeline.

## Step 1: Identify the project and CI system

Determine which project and CI to investigate:

1. **Local project context:** If in a git repository, detect the project from `git remote get-url origin` and `git branch --show-current`. Check for CI config files: `.github/workflows/`, `.circleci/config.yml`, `.gitlab-ci.yml`, `Jenkinsfile`.
2. **User-provided URL:** If the user provides a CI URL (pipeline, workflow, or job), use it directly.
3. **Ask:** If neither works, ask the user which CI system and project to investigate.

## Step 2: Check pipeline status

Quickly triage the current state:

- **Passing:** Let the user know the pipeline is green. Ask if they want to investigate a specific older failure.
- **Running:** Let the user know the pipeline is still in progress. Offer to check back or investigate a previous run.
- **Failing:** Note which workflows and jobs failed, then proceed to Step 3.

This avoids unnecessary log fetching when there is nothing to debug.

### GitHub Actions
```bash
gh run list --limit 5
gh run view <run-id>
```

### CircleCI (if MCP available)
Use `mcp__circleci-mcp-server__get_latest_pipeline_status`.

### Other
Parse the CI dashboard or ask the user for the status.

## Step 3: Fetch failure logs

Get the actual error output from failed jobs.

### GitHub Actions
```bash
gh run view <run-id> --log-failed
```

### CircleCI (if MCP available)
Use `mcp__circleci-mcp-server__get_build_failure_logs`.

### Other
Ask the user to paste the failure logs, or fetch them via `webfetch` if a URL is available.

## Step 4: Check for flaky tests

Distinguish genuine failures from intermittent issues:

- Look for tests that fail intermittently across runs (pass on retry, fail on different seeds)
- Check if the same test has failed in previous runs but passed on retry
- Look for timing-dependent tests, network-dependent tests, order-dependent tests

### GitHub Actions
```bash
gh run list --limit 20 --json conclusion,name,createdAt | python3 -c "
import json, sys
runs = json.load(sys.stdin)
from collections import Counter
c = Counter(r['name'] for r in runs if r['conclusion'] == 'failure')
for name, count in c.most_common():
    print(f'{count}x {name}')
"
```

If flaky tests are found, clearly flag which failures might be caused by flakiness rather than real issues.

## Step 5: Get detailed test results

If the failure involves test failures, get detailed metadata:

- Which specific tests failed
- Error messages and stack traces
- Test durations (slow tests may indicate timeouts)

### GitHub Actions
```bash
gh run view <run-id> --log-failed | grep -E "(FAIL|PASS|Error|panic|assert)" | head -50
```

### CircleCI (if MCP available)
Use `mcp__circleci-mcp-server__get_job_test_results` with `filterByTestsResult: 'failure'`.

## Step 6: Analyze and diagnose

Analyze the collected information directly. Do not write scripts or create temporary files to process results.

If output is too large (truncated), work through these fallbacks:

1. **Narrow to a specific job:** Fetch logs for one job at a time.
2. **Filter to failures only:** Grep for error/fail/panic/assert patterns.
3. **Ask the user:** If narrowing still truncates, ask which job or test to focus on.

Based on the collected information, provide:

1. **Root cause analysis:** What went wrong and why
2. **Flaky test identification:** Which failures (if any) are likely flaky rather than real
3. **Fix suggestions:** Concrete steps to fix the failures
4. **Code references:** If failures point to specific files/lines, read the relevant source code to provide targeted fix suggestions

## Step 7: Offer follow-up actions

After diagnosis, offer to:
- Look at the specific source code files that caused failures
- Help fix the failing tests or code
- Rerun the workflow (if CI CLI supports it)
  - GitHub Actions: `gh run rerun <run-id> [--failed]` (rerun only failed jobs)
  - CircleCI: `mcp__circleci-mcp-server__rerun_workflow` with `fromFailed: true`

## Integration with other skills

- **`systematic-debugging`** — use for the root cause tracing methodology when the CI failure is a real bug
- **`diagnosing-bugs`** — use for the disciplined diagnosis loop (red → minimise → hypothesise → instrument → fix → regression-test)
- **`tdd`** — after fixing, write a regression test that would have caught the CI failure
- **`mutation-testing`** — after fixing, consider running mutation testing on the affected area to find more gaps
