---
name: debugging
description: Use when the user says 'diagnose', 'debug this', reports something broken/throwing/failing/slow, when encountering a bug/test failure/unexpected behavior and a fix is not yet obvious, or when CI is failing and the cause needs to be found across builds, jobs, or environments.
agent: debugger
triggers: [user, model]
---

# Debugging

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom
fixes are failure. `NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.`

Two modes; full detail in `modes/<mode>.md` — read it when you enter.

| Mode | When | Detail |
|---|---|---|
| **Local** | Bug/test failure/slowness in the codebase, fix not obvious | `modes/local.md` |
| **CI** | Pipeline failing across builds/jobs/environments | `modes/ci.md` |

## Local — the discipline (summary)

1. **Phase 1 — build a feedback loop FIRST.** A tight pass/fail signal that
   goes red on *this* bug is the whole skill; bisection and instrumentation
   just consume it. Spend disproportionate effort here. Without it you cannot
   propose fixes — that is the Iron Law.
2. Then trace data flow, form hypotheses, test one at a time, fix root cause.
3. Redact every secret in shown output (`<REDACTED>`); quote only signal
   lines.

Red flags — return to Phase 1: "quick fix for now", "just try changing X",
"add multiple changes", proposing before tracing, 3+ fix attempts, each fix
revealing a new problem elsewhere.

Reference: `reference/root-cause-tracing.md`,
`reference/condition-based-waiting.md`, `reference/defense-in-depth.md`,
`scripts/hitl-loop.template.py`.

## CI — essentials

- **Access:** `gh run list/view` (GitHub), `glab ci list/view` (GitLab),
  CircleCI MCP, jenkins-cli, or parse the dashboard/logs manually.
- **Flow:** identify project+CI → check pipeline status (skip if green) →
  fetch failure logs (`gh run view <id> --log-failed`) → check for flaky
  tests (intermittent across runs/seeds) → reproduce locally → fix → verify
  by re-running the workflow.
- Distinguish real failures from flaky: same test failing intermittently or
  on retry → flag as flakiness, not the fix target.
- Never push "fixes" to make CI green without a reproduced local failure.

## Cross-skills

- `gates` — verification evidence before declaring fixed.
- `research` deep-mode — when the bug spans modules you can't trace in a pass.
