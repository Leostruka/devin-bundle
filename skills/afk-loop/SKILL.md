---
name: afk-loop
description: Use when you want the agent to work unattended through local Markdown implementation issues, picking the next ready task from a DAG of blocking relationships.
triggers: [user, model]
---

# AFK Loop

Run an unattended implementation loop over local Markdown issues.

## When to use

- The repo tracks issues as files under `.devin/scratch/<feature>/issues/*.md`.
- A human has already triaged the issues and marked them ready-for-agent.
- You want the agent to pick, implement, and resolve issues without asking for direction on each one.

## What it does

1. Reads the spec and all issue files.
2. Builds a DAG from `Blocked by:` lines.
3. Works the frontier: open, unblocked, unclaimed issues, lowest number first.
4. For each issue, runs a TDD cycle in an isolated git worktree.
5. Records the answer, marks the issue resolved, and recomputes the frontier.
6. Stops when no ready issues remain, a blocker cannot be cleared, or a human decision is required.

## Pre-flight

Before the loop starts:

- Check isolation: `git rev-parse --git-dir` and `git rev-parse --git-common-dir`. If they are the same, you are not in a worktree. Use `/using-git-worktrees` to create one or ask for consent to work in place.
- Verify the worktree path is ignored with `git check-ignore -q <path>`. If not, add it to `.gitignore` and commit first.
- Run the project baseline checks. For this bundle that is `python audit.py` and `python -m pytest tests/held-out/ -q`. Stop if not green.
- Find the effort: `glob .devin/scratch/<feature>/issues/*.md` and `read .devin/scratch/<feature>/spec.md`.
- Parse blocking edges: from each issue file, read the `Blocked by:` line and the `Status:` line.

## Frontier algorithm

A ticket is ready when:

- `Status` is not `resolved` and not `claimed`.
- Every ticket listed in `Blocked by:` has `Status: resolved`.

Pick the ready ticket with the lowest number. If none are ready:

- If all tickets are `resolved`, stop and report the feature is done.
- If at least one ticket is not resolved but not ready, stop and report the blocker and the tickets it blocks.

## Per-issue loop

For the chosen issue:

1. Set `Status: claimed` and save the file.
2. Read the issue body and the spec.
3. Run the TDD cycle inline or dispatch an `implementer` subagent with the issue as the spec. Constraints:
   - Start with a failing test.
   - Write minimal production code.
   - Refactor only after green.
   - Run the full test suite after each green.
4. When the acceptance criteria are met:
   - Append `## Answer` with a one-line gist and any context pointer.
   - Set `Status: resolved`.
   - Save the issue file.
5. Recompute the frontier.

## Ticket contract (executor-proof fields)

Issue files generated from a plan or spec SHOULD carry these fields; when
present they are binding on the implementer (contract: writing-plans
"Executor-proof plan contract"):

- `Planned at: <sha8>` - the commit the ticket was written against. Before
  implementing, run `git rev-parse --short=8 HEAD`; on mismatch treat it as
  a STOP condition: record the drift in `## Answer`, do not improvise.
- `Verify:` - the gate command(s) + expected output per step or per
  acceptance criterion. Run each gate and record the output excerpt as
  evidence; a step without a runnable gate is a ticket defect, report it.
- `STOP if:` - explicit stop conditions (drift, unverifiable step,
  out-of-scope edit needed). On trigger: stop, record the trigger in
  `## Answer`, and set `Status: blocked` with the reason instead of
  forcing a resolution.
- Report format: `## Answer` uses the executor report shape - `STATUS`,
  per-step results with files + gate excerpts, `FILES CHANGED`, `NOTES` -
  not just a one-line gist, when the ticket carried `Planned at`/`Verify:`.

## Stop conditions

Stop and report immediately if:

- No ready issue exists and at least one issue is unresolved (blocker).
- The selected issue requires a human decision.
- The work would commit or push to `main` or `master`. Ask for explicit confirmation first.
- A baseline check fails.
- The issue references Docker or a container requirement. Use the installed runtime instead; do not install Docker just to continue.

## Safety rules

- Do not `git commit` on `main` or `master`.
- Do not `git push` without explicit human confirmation.
- Do not create untracked artifacts inside the main checkout that are not in `.gitignore`.
- Worktree directories must be ignored before creation.
- The agent may commit inside the worktree only to preserve progress on a feature branch, not `main`.

## Verification

At the end of the loop, before claiming done:

- Run the project audit.
- Run the held-out test suite.
- Update the ledger with the issue status and commit SHA.

### Done grading (writer is not the grader)

The worker never gets the last word on its own DONE claim. Before setting
`Status: resolved` on an issue, grade the turn:

1. Write the issue's turn transcript (worker output tail) to a temp file.
2. Run `python scripts/done-evaluator.py --transcript <file> --task <issue.md> --strict`.
   - `not_done` (exit 4): do NOT mark resolved. Record the signals in the
     issue and continue the loop or stop per stop conditions.
   - `uncertain`: emit a grading brief (`--emit-brief`) and dispatch it to a
     separate cheap-tier model (swe-2-1-medium) - a grader that is not the
     writer. Accept `{"done": true}` only with no `missing` items.
   - `done`: proceed to mark resolved.
3. `uncertain` verdicts that the grader resolves to not-done are appended
   to `.devin/decisions.jsonl` via `scripts/decision-queue.py --add` only
   when a human decision is genuinely required.

## Cross-skills

- `/using-git-worktrees` for isolation.
- `/tdd` for the implementation cycle.
- `/verification-before-completion` before reporting done.
- `/finishing-a-development-branch` when the loop ends and the branch must be merged.
- `/adaptive-agenda-calendar-routine-engine` runs unattended issue loops inside HH:MM-HH:MM agenda blocks and the >=32-cycle verification batteries.