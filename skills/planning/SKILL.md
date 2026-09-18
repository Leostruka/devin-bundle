---
name: planning
description: Use when turning conversation into a written spec/PRD, breaking a plan or spec into independent traceable tickets, writing a concrete task-by-task implementation plan, when a decision needs external input via a questionnaire, or when planning work too large for one session as a map of decision tickets (wayfinding).
triggers: [user, model]
---

# Planning

One skill, five modes. Pick the mode that matches the need; each mode's full
detail lives in `modes/<mode>.md` — read it when you enter that mode.

| Mode | Trigger | Produces | Detail |
|---|---|---|---|
| **Spec** | "Write a spec", "turn this into a spec" | PRD from conversation context | `modes/spec.md` |
| **Tickets** | "Break this into tickets", "split into tasks" | Vertical-slice tickets with blocking edges | `modes/tickets.md` |
| **Questionnaire** | "I need to ask someone", "can't answer alone" | Questionnaire doc for external input | `modes/tickets.md` |
| **Plan-doc** | "Write the implementation plan" | Single task-by-task plan for one focused session | `modes/plan-doc.md` |
| **Wayfinder** | Work too large/foggy for one session | Map of decision tickets on the issue tracker | `modes/wayfinder.md` |

Plan-doc vs Tickets: plan-doc = one detailed plan for a single focused
session; Tickets = tracer-bullet tickets for parallel/multi-session work.

The issue tracker and triage label vocabulary should have been provided —
run `skill-discovery` if not.

## Modular atomic action mode (all modes)

Every step produced is a small, independent, verifiable atom — never a
bundled phase. Tickets/plans are sized to fit one fresh context window,
declare their own gate (`gate:` / `expect:` / `evidence:`), and are worked
one at a time: `in_progress` → run gate → `qa-ci` independent verification →
`completed`. No batching, no "we'll verify at the end." A ticket without a
defined gate is not ready-for-agent — define the gate first.

## Shared rules

- **Spec is a starting point, not a source of truth.** A PRD captures intent
  at decision time; code and `memory-management` record what actually got
  built. Don't treat the doc as gospel once hotfixes land.
- **Vertical slices, not horizontal phases.** Each task cuts a complete path
  through every layer — demoable on its own. Wide refactors are the
  exception: sequence expand–contract.
- **Declare proposed modules/interfaces first.** The contract surface a
  reviewer checks; prevents horizontal decomposition.
- **DRY. YAGNI. TDD. Frequent commits.**
- **Living vs disposable assets.** Prefix scratch files `tmp_`/`prototype_`;
  the plan includes their deletion step.

## Cross-skills

- Invoke `research` (deep mode) before Spec if the codebase is unfamiliar or large.
- Invoke `context7` when the spec depends on a library's current API.
- Invoke `execution`'s review-cadence guidance if unsure whether the request
  needs full planning or can move straight to implementation.
- `reference/plan-document-reviewer-prompt.md` — reviewer prompt for checking
  a finished plan doc.
