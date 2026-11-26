---
name: council
description: Use when a high-stakes change needs independent multi-model review before merge - several strong reviewers in parallel, iterating rounds until they are satisfied, with scores and costs ledgered. Distinct from arena (competing builders); council reviews one finished change.
triggers: [user, model]
---

# Council

Independent parallel review of one finished change by several reviewers,
iterated in rounds. Source pattern verified in `t3dotgg/tstack` council
(evidence `.devin/research/media-osint-20261126-yt2/external/tstack_council_SKILL.md`),
hardened with bundle cost and evidence discipline.

Council is expensive. Use it for high-risk diffs (security, data model,
public API, irreversible operations, large refactors) or when the user
asks. A normal change gets `code-review`, not a council.

## Before round 1

1. Fix every issue you already know about. Council rounds spent on known
   bugs are wasted money.
2. Run the project checks. Do not convene a council on a red tree.
3. Write the review packet once: the diff or branch range, the spec or
   acceptance criteria, and the explicit question (usually: is this correct
   and safe to merge). Every delegate gets the same packet.

## Delegates

- One strong reviewer per provider when several providers are available,
  high reasoning effort, all spawned in parallel.
- Delegates are read-only: they review and report, they never edit.
- Delegates are independent: none sees another delegate's review before
  submitting. Shared context collapses independent judgment into
  correlation (same failure as target leakage in `impeccable`).
- If a named provider or model is unavailable, report the degradation and
  continue with what exists. Never silently substitute and never label a
  single-provider panel as multi-provider. Under the free-model policy all
  seats may run the same model; differentiate by review angle (correctness,
  security, simplicity) and mark the panel `degraded: single-provider`.
- Do not wait idle. While delegates run, verify early findings against the
  code yourself. Do not edit files in a checkout still under review.

## Rounds

- One full pass of all blocking delegates is one round. Count them.
- Ask each delegate for a score out of 10 plus findings with file:line.
- A delegate that fails or times out is non-blocking: mark it in the table,
  never invent its score, never count it as approval.
- Iterate until the blocking delegates are satisfied or the budget is
  spent. Each round must close at least one finding; a no-progress round
  ends the loop.
- Resist scope creep actively: findings outside the diff's purpose are
  filed as separate issues, not fixed in this change. A council that keeps
  growing the diff never terminates.

## Cost discipline

- Set the budget before round 1: max rounds (default 3) and max spend.
- Escalate cheap to expensive: a single strong reviewer first, full
  council only when the diff is high-risk or the first pass disagrees
  with itself. Unbounded iteration is a cost failure mode (source
  evidence: ~956M tokens for one UI campaign).
- Log rounds in `.devin/ledgers/council-<change>.md`: round, delegate,
  provider/model, score, findings count, cost, verdict.

## Output

The review result is a table, in the PR description when there is one:

| round | delegate | model/provider | score | status |
|---|---|---|---|---|
| 1 | correctness | example/example | 8/10 | blocking |
| 1 | security | unavailable | no score | non-blocking |

`no score` when missing, never invented. State the round count, the final
verdict, and what was deferred out of scope.

## Cross-skills

- `code-review` - the per-delegate review discipline; council orchestrates,
  code-review is how each seat reviews.
- `arena` - competing builders for the artifact itself; use arena before
  council when the shape is undecided, council after a shape exists.
- `agent-cost-guard` - budget enforcement across rounds.
