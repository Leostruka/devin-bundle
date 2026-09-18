---
name: testing
description: Use when implementing any feature or bugfix and a test-driven approach is appropriate (red-green-refactor, seams-first), or when the user asks to find testing gaps, mutation test, or identify surviving mutants.
triggers: [user, model]
---

# Testing

Two modes; full detail in `modes/<mode>.md`. Reference:
`reference/writing-good-tests.md`, `reference/mocking.md`,
`reference/tests.md`.

| Mode | When | Detail |
|---|---|---|
| **TDD** | Implementing a feature/bugfix test-first | `modes/tdd.md` |
| **Mutation** | Finding coverage gaps via surviving mutants | `modes/mutation.md` |

## TDD — the contract

```
RED → verify RED → GREEN → verify GREEN → REFLECT → REFACTOR
```

**Iron law: NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.** Code written
before the test gets deleted — not kept, not adapted. Verify RED fails for
the expected reason (feature missing, not a typo). REFLECT: could a wrong
implementation pass? Then the test is too weak — rewrite before continuing.

Seams-first: agree WHERE to test (public interface, highest seam) before
writing tests; the iron law enforces HOW. Refactoring → characterization
tests first. Bug fix → failing test reproducing the bug at the right seam.
Throwaway prototype → confirm with user, then skip.

## Mutation testing — essentials

A mutant = small deliberate change mimicking a realistic bug. Killed = tests
fail (good). Survives = tests pass → coverage gap.

Priority targets: security/auth checks, control-flow inversions, validation
removal, state/constant alteration, swallowed errors. Bias toward survivors:
boundary conditions, error paths, recently changed code.

Never mutate: test code/helpers/fakes, logging-only blocks, generated/vendored
code. Verify each mutant compiles/loads; report killed vs survived with the
mutations that exposed gaps.
