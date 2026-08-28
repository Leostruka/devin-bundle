---
name: review-cadence
description: Use when deciding how much human review and upfront planning a task needs based on its size, risk, and blast radius, or when the user asks whether a change can skip grilling and go straight to implementation.
---
# Review Cadence

## Overview

Not every change needs the same checkpoints. Big, risky work should be aligned on early and reviewed before shipping. Small, safe work can be described in one prompt and reviewed only at the end. This skill decides where to place the planning and review checkpoints.

## When to use

- The user says "just change the color of a button" or "rename this".
- The user has a small bug fix that is only a couple of lines.
- You are deciding whether to run `grilling` / `wayfinder` or go straight to `implement`.
- You want to explain why a task needs more or less human alignment.

## Decision tree

```
Is the task well-understood and low-risk?
├── No → Is the change large or does it span multiple subsystems?
│   ├── Yes → Shift planning LEFT: use `grilling` (With-docs mode) or `wayfinder`
│   └── No  → Shift planning LEFT: use `grilling` (Stateless mode) to align
└── Yes → Can the change be verified by a single command or diff?
    ├── Yes → Shift review RIGHT: one prompt → `implement` → `code-review`
    └── No  → Shift review RIGHT: one prompt → `implement` → manual verification gate
```

## Definitions

- **Shift planning left**: align with the human before the work starts. Use `grilling`, `grilling` with docs, or `wayfinder` for large/risky/ambiguous tasks.
- **Shift review right**: do the work first, then review it. Appropriate for small, safe, reversible changes (rename, color tweak, two-line bug fix, internal doc edit).
- **Blast radius**: how many other systems or files a change can affect.

## Observable predicates

| If this is true | Then | Because |
|-----------------|------|---------|
| Change is a refactor, rename, color, or copy tweak | Review right, single prompt | Easy to regenerate, cheap to revert, easy to diff |
| Bug fix is < 10 lines and isolated | Review right, single prompt | Small diff fits in context; review at end is enough |
| New feature or behavior | Review both left and right | Align on the design first, then review the diff |
| Change touches public API, auth, permissions, or critical path | Review both left and right | High blast radius; mistakes are expensive to fix later |
| The user says "grill me" or "I need to think this through" | Review left | Explicit request for upfront alignment |
| The request is vague or the scope is unknown | Review left | Cannot safely implement without shared understanding |

## Anti-patterns

- **Over-planning a rename**: don't run `grilling` just to change a title.
- **Under-planning a feature**: don't `implement` a multi-file feature from a one-sentence prompt.
- **One-size-fits-all**: "always grill" and "never grill" are both wrong; use the predicates above.

## Cross-skills

- Use `grilling` when the result is "review left".
- Use `implement` and then `code-review` when the result is "review right".
- Use `wayfinder` when the work is huge, foggy, or too big for one session.
