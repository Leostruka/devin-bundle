---
name: executing-plans
description: Use when executing a written implementation plan with checkpoints and reviews.
---
# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Modular atomic action mode.** Each plan task is one atomic, verifiable action — never a bundled phase. Tasks are worked one at a time: `in_progress` → run the task's gate → dispatch the `qa-ci` subagent for independent verification → `completed`, then the next task. No batching, no "we'll verify at the end." A plan task without a defined gate is a gap — raise it with your human partner before starting.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** This skill works best when subagents are available (Devin CLI supports `run_subagent`). If the plan has independent tasks that benefit from fresh contexts, use `/dispatching-parallel-agents` instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Ensure an isolated workspace: use /using-git-worktrees to create one or verify the existing one
2. Read plan file
3. Review critically - identify any questions or concerns about the plan
4. If concerns: Raise them with your human partner before starting
5. If no concerns: Create todos for the plan items and proceed

### Step 2: Execute Tasks (atomic, one at a time)

For each task:
1. Mark as `in_progress`
2. Confirm the task has a defined gate (`gate:` command, `expect:` output/exit code, `evidence:` ledger/file). If missing, stop and raise the gap — do not start without a gate.
3. Follow each step exactly (plan has bite-sized steps)
4. Run the task's gate yourself and capture output + exit code
5. If the task touches unfamiliar code or a library, invoke `deep-mode` or `context7` first
6. **Independent QA/CI verification (anti-gaming):** dispatch the `qa-ci` subagent (`swe-1-7`, no write tools) to re-run the gate on a clean checkout, run `tests/held-out/` if present, and audit the diff for overfitting (hard-coded constants, mocked gates, skipped tests, phantom guardrails). The QA/CI subagent sees only the diff and the spec — never your report.
7. Mark as `completed` only when the `qa-ci` subagent returns `Verdict: PASS` with fresh command output + exit code as evidence. If QA/CI returns `FAIL`, keep the task `in_progress`, feed the failure back, and re-enter the fix loop. Never override a QA/CI FAIL with self-report.

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use /finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Never mark a task `completed` without an independent `qa-ci` PASS
- Never override a `qa-ci` FAIL with self-report, "should work", or confidence
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Cross-skills

- Before finishing, `finishing-a-development-branch` (already required in Step 3) closes with `code-review` and `verification-before-completion`.
- If the plan changes in size or risk mid-flight, invoke `review-cadence` to decide whether to keep the same checkpoint cadence.
