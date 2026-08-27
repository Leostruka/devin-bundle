---
name: implement
description: Use when the user wants to implement a feature or fix from a spec or set of tickets.
---
Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams. If the ticket touches an unfamiliar library or a broad swath of the codebase, invoke `context7` or `deep-mode` before writing code.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

Commit your work to the current branch.
