---
name: execution
description: Use when executing a written implementation plan with checkpoints, when implementing a feature/fix from a spec or tickets, when deciding how much human review and upfront planning a task needs, or when working unattended through local Markdown issues in a blocking DAG (AFK loop).
triggers: [user, model]
---

# Execution

The implement side of plan→ship: cadence decision → implement → execute plan
tasks atomically → (optionally) unattended AFK loop over issue DAGs.

## Review cadence (decide first)

Not every change needs the same checkpoints.

```
Is the task well-understood and low-risk?
├── No → large/multi-subsystem? → planning LEFT: `grilling` or `planning` wayfinder
│        small but ambiguous?   → planning LEFT: `grilling` (stateless)
└── Yes → verifiable by one command/diff? → review RIGHT: prompt → implement → `code-review`
          otherwise → review RIGHT: prompt → implement → manual verification gate
```

| If true | Then |
|---|---|
| Refactor, rename, color/copy tweak | Review right, single prompt |
| Bug fix <10 lines, isolated | Review right, single prompt |
| New feature or behavior | Review both left and right |
| Touches public API, auth, permissions, critical path | Review both left and right |
| Request vague or scope unknown | Review left |

Anti-patterns: grilling a rename; implementing a multi-file feature from a
one-sentence prompt; "always grill" / "never grill".

## Implement

- Surgical, goal-driven changes; don't refactor unrelated code.
- Keep the PR small — target ~300 lines; >500 → split first (`intake`).
- Define input/output of the change (request/response contract, data ownership).
- Never delete/disable/skip tests without explicit user approval.
- TDD at pre-agreed seams; `context7`/`research` for unfamiliar libs or code.
- Run typecheck + single test files regularly; full suite once at the end.
- Then `code-review` → verification gate (see `gates`) → commit to the branch.
  API/DB/secrets/endpoints/infra changes → also `security`.

## Executing a plan

Load plan → review critically (raise concerns before starting) → todos →
execute tasks **atomically, one at a time**:

1. Mark `in_progress`.
2. Confirm the task's gate (`gate:` / `expect:` / `evidence:`). Missing →
   stop, raise the gap — don't start without a gate.
3. Follow steps exactly; run the gate yourself, capture output + exit code.
4. **Independent QA/CI (anti-gaming):** dispatch `qa-ci` subagent
   (`swe-2-medium`, no write tools) to re-run the gate on a clean checkout,
   run `tests/held-out/` if present, and audit the diff for overfitting
   (hard-coded constants, mocked gates, skipped tests, phantom guardrails).
   QA/CI sees only diff + spec — never your report.
5. `completed` only on `Verdict: PASS` with fresh output. QA/CI FAIL → keep
   `in_progress`, feed back into the fix loop. Never override FAIL with
   self-report.

**Stop and ask** on: blockers, critical plan gaps, unclear instructions,
repeated verification failure. Never start implementation on main/master
without explicit consent. Finish with `finishing-a-development-branch`.

## AFK loop (unattended Markdown issues)

For repos tracking issues under `.devin/scratch/<feature>/issues/*.md` with
`Blocked by:` edges, already triaged `ready-for-agent`:

**Pre-flight:** verify worktree isolation (`git rev-parse --git-dir` vs
`--git-common-dir`); worktree path gitignored; baseline checks green
(`python audit.py`, `pytest tests/held-out/ -q`); read spec + issue files;
parse `Blocked by:` / `Status:`.

**Frontier:** a ticket is ready when `Status` ∉ {resolved, claimed} and all
`Blocked by:` tickets are resolved. Pick lowest number. None ready + all
resolved → done. None ready + unresolved exist → report blocker.

**Per issue:** `Status: claimed` → read body+spec → TDD cycle (or
`implementer` subagent with the issue as spec: failing test → minimal code →
refactor on green → full suite) → on acceptance: append `## Answer` gist,
`Status: resolved`, recompute frontier.

**Stop conditions:** blocker; human decision required; would commit/push to
main/master; baseline check fails; issue requires Docker (use installed
runtime instead).

**Safety:** never commit on main/master; never push without confirmation; no
untracked artifacts outside `.gitignore`; worktree commits only on feature
branch. End of loop: audit + held-out suite + ledger update with status and
commit SHA.
