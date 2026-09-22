---
name: code-review
description: Use when completing a task, reviewing a branch or PR, before merging, when the user asks to 'review since X', when publishing a GitHub PR review with inline comments/suggestions, or when the user receives code review feedback and needs to decide how to act on it.
triggers: [user, model]
---

# Code Review

Three modes; full detail in `modes/<mode>.md` — read it when you enter the
mode. `code-reviewer.md` is the reviewer subagent brief.

| Mode | When | Detail |
|---|---|---|
| **Giving** | Completing a task, reviewing a branch/PR, before merge, "review since X" | `modes/giving.md` |
| **PR-inline** | Publishing a GitHub review with inline ` ```suggestion ` comments | `modes/pr-inline.md` |
| **Receiving** | Deciding how to act on review feedback you received | `modes/receiving.md` |

## Giving — essentials

- Review the diff against the spec, not your memory of it.
- Two-axis review where the repo defines it (Standards vs Spec).
- Every finding cites file:line and the rule it violates.
- Verify claims with tools before reporting — no "looks fine" without evidence.
- Independent reviewer subagent (`reviewer`/`qa-ci`) for unbiased assessment
  on high-risk diffs.

## PR-inline — essentials

- Cycle: CHECK → COMMENT/SUGGEST → NEXT. One concern per cycle; never post
  before confirming the target line in the PR head.
- `gh api` with `--field` for per-line positioning (not `gh pr review`).
- ` ```suggestion ` blocks must be applicable in one click.
- Don't edit the PR's code locally; comments only.
- Comment language follows the repository.
- Every comment gets a gate in the ledger (see `gates`).

## Receiving — essentials

Verify before implementing; ask before assuming; technical correctness over
social comfort.

1. READ the feedback completely without reacting.
2. UNDERSTAND — restate the requirement or ask.
3. VERIFY against codebase reality.
4. EVALUATE — technically sound for THIS codebase?
5. RESPOND — technical acknowledgment or reasoned pushback.
6. IMPLEMENT — one item at a time, test each.

Classify each item: **pushed** (reviewer cites a concrete violation → verify
against the cited source, fix, test) vs **pulled** (reviewer points to a
skill/convention/gate you should have used → pull that source first, apply,
verify). Repeated missing pulled patterns → add to your pre-review checklist.

## Cross-skills

- `security` — escalate to the security skill when the diff touches auth, secrets, input handling, or public endpoints.
- `a11y-audit` — escalate when the diff touches frontend markup/ARIA/keyboard paths.

against the cited source, fix, test) vs **pulled** (reviewer points to a
skill/convention/gate you should have used → pull that source first, apply,
verify). Repeated missing pulled patterns → add to your pre-review checklist.
