---
name: afk-loop
description: Use when you want the agent to work unattended through local Markdown implementation issues, picking the next ready task from a DAG of blocking relationships.
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

## Cross-skills

- `/using-git-worktrees` for isolation.
- `/tdd` for the implementation cycle.
- `/verification-before-completion` before reporting done.
- `/finishing-a-development-branch` when the loop ends and the branch must be merged.