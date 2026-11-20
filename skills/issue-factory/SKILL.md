---
name: issue-factory
description: Use when running a batch of ready implementation issues through one "factory" pipeline - intake and risk tiering, parallel implementer subagents in per-issue worktrees, graded gates, risk-tiered review, one PR per issue - instead of working issues one at a time. Composes afk-loop, dispatching-parallel-agents, git-workflows, and pr-review; for the sequential unattended variant use afk-loop.
triggers: [user, model]
---

# Issue Factory

One command ("factory run") processes every ready issue end to end:
intake -> build -> gate -> review -> PR. An orchestrator (this session)
keeps the board; workers own branches. Adapted from the
issues-to-PRs factory pattern (zazencodes software-factory reel, 2026-11):
our equivalent of that pipeline is this skill plus the existing DAG,
worktree, grading, and review machinery.

## When to use

- 2+ issues are ready-for-agent under `.devin/scratch/<feature>/issues/`
  (or `gh issue list --label ready-for-agent`) AND mostly independent.
- You want parallel lanes, per-issue PRs, and a board you can re-read
  after compaction.
- Sequential or single-issue work: use `/afk-loop` instead.

## Pre-flight

1. Baseline green: `python audit.py` + `python -m pytest tests/held-out/ -q`.
   Stop on red.
2. Issue inventory: `glob .devin/scratch/<feature>/issues/*.md` or
   `gh issue list`. Parse `Status:` and `Blocked by:` lines into the DAG.
3. Worktree root ignored: `git check-ignore -q <worktree-root>`; add to
   `.gitignore` and commit if not.
4. Open the board: `.devin/ledgers/<feature>-factory.md` with one row per
   issue: `| issue | lane | risk | status | pr | sha | notes |`.
   Every dispatch is also recorded via
   `python scripts/subagent-trace.py record` (see
   dispatching-parallel-agents, dispatch trace contract).

## Intake and risk tier

For each ready issue, write `Risk:` into the issue file:

- **low**: single module, has tests, reversible. Review by `reviewer`
  (cheap tier suffices).
- **high**: cross-module, security/data path, missing tests, or unclear
  spec. Review by `reviewer` with a second `code-review` pass, or route
  the build itself to a stronger model (`subagent_general`).

Ambiguous spec or acceptance criteria: send to `/intake` first, do not
build.

## Factory loop

1. Recompute the frontier (afk-loop rules: open + unblocked + unclaimed).
2. Dispatch one `implementer` subagent per ready issue, all in one
   response so they run in parallel. Each prompt carries: the issue file
   path, spec pointer, an exclusive worktree path
   (`/using-git-worktrees`, one lane per issue, `git-workflows` lane
   ownership), the TDD contract, and "commit on the lane branch only".
   Respect `data/bundle-models.json` tiers: low risk builds on the cheap
   profile; high risk on `subagent_general`.
3. As each worker returns: run `scripts/done-evaluator.py --strict` on its
   transcript (afk-loop done-grading; the writer is not the grader).
   `not_done` -> requeue once with the signals; twice -> escalate tier or
   mark the issue blocked with the reason.
4. On `done`: risk-tiered review. low -> `reviewer` subagent on the diff;
   high -> `reviewer` plus a `code-review` pass. Findings route back as a
   fix round (dispatching-parallel-agents fix-round rules, R<=5).
5. Clean review -> `/finishing-a-development-branch`: merge to the
   integration branch and open one PR per issue
   (`gh pr create`, `Closes #<n>`) unless the user wants local-only.
6. Update the board row and the issue `Status:` (`resolved`, `blocked`,
   or `pr-opened`) after every transition. The board is the state; do not
   rely on memory.

## Stop conditions

- A lane needs `main`/`master` commits or a push without confirmation.
- A worker cannot clear its blocker after one requeue.
- Baseline checks go red mid-run.
- Two issues collide on the same files (kill one lane, mark dependency,
  re-serialize through `/afk-loop`).

## Verification

Before declaring the run done: all issue rows terminal, `python audit.py`
green, full `pytest -q` green on the integration branch, and the board
appended to the run ledger. Report per issue: PR link or lane SHA,
grading verdict, review findings count.

## Cross-skills

- `/afk-loop` - sequential unattended variant; DAG and grading rules live there.
- `/dispatching-parallel-agents` - prompt structure, profile table, trace contract.
- `/using-git-worktrees` + `/git-workflows` - lane isolation and ownership.
- `/pr-review` + `/code-review` - the review stage.
- `/effort-calibration` - risk-to-model mapping rationale.
