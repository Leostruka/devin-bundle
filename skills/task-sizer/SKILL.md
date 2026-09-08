---
name: task-sizer
description: Use when estimating the size of a task or PR and deciding whether to split it into smaller tickets before implementation.
---

# Task Sizer

Estimates the size of a task or PR and recommends splitting when it exceeds reviewable or safe limits. Keeps changes small, verifiable, and easy to review.

## When to use

- Before implementing a feature or fix.
- When a task touches multiple files or systems.
- When the user asks for a large change without a clear breakdown.
- When the PR size is unknown or likely to exceed limits.

## Size limits

| Limit | Action |
|-------|--------|
| ~300 lines | Target size for a single PR. |
| ~500 lines | Split into smaller tickets or vertical slices. |
| >500 lines | Must be decomposed before implementation. |

## What to estimate

- **Lines of code** to be added, modified, or deleted.
- **Files touched** — more files = more review surface.
- **System boundaries** — crossing API, DB, or auth boundaries increases risk.
- **Test coverage** — new code needs tests; tests add to the diff size.

## Process

```
Estimate task size
  → If ~300 lines: proceed as single PR
  → If ~500 lines: split into smaller tickets
  → If >500 lines: decompose before implementing
  → If boundaries unclear: ask for clarification or split by boundary
```

## Example

```
Task: Add user authentication to the API
Estimate: ~600 lines (middleware, routes, tests, docs)
Decision: Split into 2 tickets:
  - Ticket 1: Auth middleware + tests (~300 lines)
  - Ticket 2: Routes + docs (~300 lines)
```

## Anti-patterns

- Implementing a >500 line change in one PR.
- Estimating only the "happy path" and ignoring tests.
- Splitting by arbitrary file count instead of logical boundaries.
- Skipping the size check because "it's just a small feature."

## Cross-skills

- `planning-pipeline` — uses task size to split tickets.
- `implement` — enforces the ~300/~500 limits during execution.
- `effort-calibration` — larger tasks need higher effort; smaller tasks need less.
- `verification-before-completion` — verifies the PR size was respected.
