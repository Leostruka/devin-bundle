---
name: implement
description: Use when the user wants to implement a feature or fix from a spec or set of tickets.
---
Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams. If the ticket touches an unfamiliar library or a broad swath of the codebase, invoke `context7` or `deep-mode` before writing code. If you are unsure whether this task can skip upfront planning and go straight to code, invoke `review-cadence` first. If the task is trivial or unusually hard, invoke `effort-calibration` to choose the right reasoning level.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work, then `verification-before-completion` before declaring it done.

Commit your work to the current branch.
