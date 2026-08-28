---
name: autonomous-gates
description: Use when running long-horizon or multi-step tasks where quality must be verified before proceeding, when the user asks for "autonomous mode" or "run unattended", or when a task has explicit acceptance criteria that must pass before declaring done.
---

# Autonomous Gates

## When to Use

- Task has explicit acceptance criteria (tests pass, build succeeds, lint clean)
- User asks for autonomous or unattended execution
- Multi-step task where each step's output feeds the next
- Long-horizon work where drift or skipping steps is a risk
- Before declaring a task "done" — the final gate

## When NOT to Use

- Single-step task with immediate feedback — just do it and report
- Task has no verifiable criteria — ask the user what "done" means
- Gate command doesn't exist yet — define it first, then use it

## Source

Adapted from PrimeAgent's autonomous mode (PrimeIntellect blog, 2026-08-05).
PrimeAgent supports `--autonomous --autonomous-gate "npm run check"
--autonomous-max-turns 20`. The gate runs before the session is allowed to
finish. A failed gate returns its bounded output to the agent for another
attempt. PrimeAgent skips rerunning a failed gate when the workspace has not
changed since the last attempt.

## Core Concept

A **gate** is a command that must pass (exit 0) before the task can be
declared complete. Gates are:
- **Bounded** — output is truncated to avoid flooding context
- **Idempotent** — running twice with no changes gives the same result
- **Skippable on no-change** — if nothing changed since last failure, don't rerun
- **Multi-level** — different gates for different stages of the task

## Gate Types

| Gate type | When | Example command | Failure action |
|---|---|---|---|
| Pre-task | Before starting work | `git status --porcelain` (confirm clean state) | Stop and ask user |
| Step gate | After each major step | `npm run test -- --grep "<step>"` | Retry step with failure output |
| Integration gate | After combining steps | `npm run build` | Rollback to last green state |
| Final gate | Before declaring done | `npm run check` (lint + typecheck + test) | Cannot declare done; continue working |
| Security gate | Before any push | `python scripts/check-ai-signature.py` | Block push, fix signature |

## Workflow

### Step 1: Define gates at planning time

When creating the todo list, add a gate to each task that has verifiable
criteria:

```
todo: "Implement auth module"
gate: "npm run test -- --grep auth"
```

### Step 2: Run gate after each step

After completing a step, run its gate:

```
exec: npm run test -- --grep auth
```

If exit code != 0:
1. Read the output (bounded — first 50 lines usually suffice)
2. Fix the issue in the inner loop
3. Rerun the gate
4. If the workspace hasn't changed since last failure and gate still fails,
   stop and escalate — the gate may be wrong, not the code

### Step 3: Run integration gate after combining steps

After multiple steps are complete:

```
exec: npm run build && npm run test
```

If this fails but individual step gates passed, the issue is in the
integration — trace the interaction between steps.

### Step 4: Run final gate before declaring done

The final gate is the complete check suite:

```
exec: npm run check  # or: lint + typecheck + test + build
```

**No declaration of "done" without the final gate passing.** This is
enforced by Rule 5 (No push without green) and Rule 10 (Don't declare
without verifying).

### Step 5: Bounded output

If a gate produces very long output, bound it:

```
exec: npm run check 2>&1 | head -100
```

Don't let gate output flood the context — that defeats the purpose.

## Idempotency and No-Change Skip

If a gate fails, you fix something, and rerun:
- If the fix changed relevant files → rerun the gate
- If the fix was unrelated (e.g., docs change) → gate result is unchanged, skip rerun
- If unsure → rerun (safer)

## Multi-Level Example

Task: "Add OAuth2 login with Google"

```
Step 1: Install passport-google-oauth20
  Gate: npm ls passport-google-oauth20  # confirm installed

Step 2: Implement Google strategy
  Gate: npm run test -- --grep "google strategy"

Step 3: Implement login route
  Gate: npm run test -- --grep "login route"

Step 4: Implement callback route
  Gate: npm run test -- --grep "callback route"

Integration gate: npm run test -- --grep "auth"
Final gate: npm run check
Security gate: python scripts/check-ai-signature.py
```

## Anti-Patterns

- **Don't declare done without the final gate.** "I think it works" is not a gate result.
- **Don't skip gates to save time.** A skipped gate is an unverified step.
- **Don't use gates as the only verification.** Gates catch regressions; manual review catches design issues. Use both.
- **Don't make gates too broad.** `npm test` as a step gate runs everything — use scoped gates (`--grep`).
- **Don't ignore a failing gate.** A failing gate means the task is not done. Fix it or escalate.

## Integration with Existing Skills

- **`unlazy`:** for long-horizon tasks, write a `.devin/ledgers/<task>.md` with gates before starting. `autonomous-gates` executes those gates.
- **`review-cadence`:** decide how many planning and review checkpoints the task needs before building the gate list.
- **`handoff`:** if work spans sessions, capture the current gate state before ending.
- **`verification-before-completion` skill:** defines per-task VFs; gates execute them
- **`check-push-green.py` hook:** already enforces the push gate at the hook level

## Integration with Existing Rules

- **Rule 5 (No push without green):** the final gate IS the green check
- **Rule 10 (Don't declare without verifying):** gates are the verification mechanism
- **Rule 11 (Never fail from failures):** a failing gate is a signal to fix, not to stop

## Evidence Summary

| Claim | Source | Status |
|---|---|---|
| PrimeAgent `--autonomous-gate` runs before session finishes | PrimeAgent blog | Verified |
| Failed gate returns bounded output to agent | PrimeAgent blog | Verified |
| Skips rerunning failed gate when workspace unchanged | PrimeAgent blog | Verified |
| `--autonomous-max-turns` bounds continuation | PrimeAgent blog | Verified |
