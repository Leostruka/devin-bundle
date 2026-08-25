---
name: unlazy
description: Use when a task is at risk of agent laziness (large, multi-step, previously half-done, or with clear acceptance criteria) to force proof of completion through a gates ledger instead of trusting agent reports.
---

# Unlazy

## When to Use

- Long-horizon or multi-step task where the agent might stop early
- Task with many files and parts; the agent has previously skipped hard ones
- User asks for a large feature/refactor and wants proof, not claims
- Need to prevent "done" announcements that cannot be verified

## When NOT to Use

- Single-step task with immediate verifiable output
- Task has no clear acceptance criteria
- Overhead of a ledger is not justified (small fix, <20 lines, one tool call)

## Source

Adapted from Leonxlnx's `unlazy` skill for Claude Code / Codex
(`https://raw.githubusercontent.com/Leonxlnx/unlazy/main/SKILL.md`),
which enforces completion discipline by writing acceptance gates before
execution, decomposing work with the Depth Tree, and re-verifying evidence
before reporting. This is a Devin CLI adaptation.

## Core Concept

Agent laziness shows up in two ways:
1. The agent claims it is done when it is not.
2. The agent shrinks the job without telling you (skips the hard part).

The `unlazy` pattern forces the agent to **prove** completion instead of
declaring it. It does this with three mechanisms:

1. **Gates ledger:** A `.devin/ledgers/<task>.md` file where every subtask
   has one gate with:
   - **Outcome:** what must be true
   - **Check:** the exact command that proves it
   - **Expect:** the string or exit code that proves it
   - **Evidence:** empty until the checker fills it

2. **Independent verification:** After the agent claims a step is done, the
   agent itself (or a `reviewer` subagent) re-runs the check. The result must
   match the expected output. A ticked gate with `EVIDENCE: pending` is worse
   than an empty gate; it means the agent is still only telling you it is done.

3. **Honest abandonment:** If a step is impossible, the agent writes an
   explicit `ABANDON` line with a reason instead of dropping it silently.

## Ledger Format

```markdown
# GATES: add OAuth2 login

- [ ] G1: valid fixture imports completely
  CHECK: python -m pytest tests/import/test_valid.py
  EXPECT: 1 passed
  EVIDENCE: pending

- [ ] G2: package-level integration succeeds
  CHECK: python -m pytest tests/integration/test_package.py
  EXPECT: 1 passed
  EVIDENCE: pending

- [ ] G3: migration wording is reviewed
  EVIDENCE: pending

ABANDON: G3 migration owner unavailable; recorded in issue 123
```

Rules for runnable gates:
- Give every runnable gate both `CHECK:` and `EXPECT:`.
- Run the check. If it passes, replace `EVIDENCE: pending` with the snippet
  that decided it (or `EVIDENCE: ok`).
- If the check fails, leave `EVIDENCE` empty and fix the work, not the check.
- Manual gates (no `CHECK:`) are allowed only when no command can decide.

## Workflow

1. **Plan the task:**
   - Break the task into subtasks at natural boundaries.
   - Each subtask should be a coherent deliverable that can be verified.

2. **Write the ledger first:**
   - Create `.devin/ledgers/<task>.md` before doing the work.
   - Every subtask gets at least one gate.

3. **Work each subtask:**
   - Implement the deliverable.
   - Run the gate.
   - Record evidence.
   - If impossible, write `ABANDON: <id> <reason>`.

4. **Verify before reporting:**
   - Re-run every runnable gate after the work is claimed done.
   - Report met, unmet, and abandoned counts.
   - Do not report "done" while any required gate is unmet or abandoned.

## Integration with Existing Skills

- `autonomous-gates` — gate semantics, bounded output, idempotency
- `dispatching-parallel-agents` — parallel subagents for independent leaves
- `verification-before-completion` — evidence before claims
- `using-git-worktrees` — isolate orchestrated runs
- `writing-plans` — structure the plan file

## Anti-Patterns

- Do not let the agent grade its own gates without re-running the check.
- Do not trust "done" without recorded evidence.
- Do not skip the `ABANDON` line for impossible steps.
- Do not create a ledger for a trivial edit.
