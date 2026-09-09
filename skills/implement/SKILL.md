---
name: implement
description: Use when the user wants to implement a feature or fix from a spec or set of tickets.
triggers: [user, model]
---
Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams. If the ticket touches an unfamiliar library or a broad swath of the codebase, invoke `context7` or `deep-mode` before writing code. If you are unsure whether this task can skip upfront planning and go straight to code, invoke `review-cadence` first. If the task is trivial or unusually hard, invoke `effort-calibration` to choose the right reasoning level.

## Scope and size

- Make surgical, goal-driven changes. Touch only what the task requires; do not refactor unrelated code.
- Keep the PR small. Target ~300 lines; if the change exceeds ~500 lines, split it into smaller tickets before implementing.
- Define the input and output of the change. For APIs, that is the request/response contract; for services, the interface and data ownership.
- Do not delete, disable, or skip tests without explicit user approval.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work, then `verification-before-completion` before declaring it done. If the change touches API, DB, secrets, endpoints, or infrastructure, also run `security-audit`.

Commit your work to the current branch.
