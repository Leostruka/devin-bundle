---
name: thermos
description: Use when launching both thermo-nuclear review subagents in parallel and synthesizing their findings, for thermos, double thermo review, or combined bug/security and code-quality branch audits.

disable-model-invocation: true
---

# Thermos

Vendored from cursor/plugins `thermos` (MIT license, (c) Cursor); orchestration adapted to Devin `run_subagent` mechanics.

Run the two thermo review passes as async background subagents in parallel, then synthesize their results.

## Workflow

1. Determine the review scope from the user request, PR, current branch, or relevant changed files.
2. Gather the diff and any file/context excerpts needed for reviewers to evaluate the change without guessing.
3. Launch both lanes in the same block with `run_subagent(profile="reviewer", is_background=true)`:
   - Lane 1: `agents/thermo-nuclear-review-subagent.md` for bugs, breakages, security, devex regressions, feature-flag leaks, and other branch-audit risks.
   - Lane 2: `agents/thermo-nuclear-code-quality-review-subagent.md` for maintainability, structure, file-size growth, spaghetti, abstractions, and codebase-health risks.
4. Pass each subagent the same scoped diff/file context and ask it to return prioritized findings with file references and evidence.
5. After both finish, synthesize the results with findings first, deduplicated across reviewers. Weight overlapping findings more heavily, resolve disagreements with your own judgment, and keep summaries brief.

If individual background summaries are already visible to the user, do not restate them wholesale. Surface the unified verdict, the highest-signal findings, and any remaining uncertainty.
