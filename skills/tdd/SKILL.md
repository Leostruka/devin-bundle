---
name: tdd
description: Use when implementing any feature or bugfix and a test-driven approach is appropriate.
---
# Test-Driven Development (Unified)

Two traditions, one loop. This skill merges the **iron-law discipline** (tests-first, no exceptions, watch them fail) with the **seams-first operational approach** (agree on test boundaries, vertical slices, avoid anti-patterns).

## The Red-Green-Refactor Contract

The only acceptable order is:

```
RED      → verify RED
GREEN    → verify GREEN
REFLECT  → can this test be cheated?
REFACTOR → while green
```

1. **RED**: write one failing test before any production code.
2. **Verify RED**: run it. It must fail for the expected reason (feature missing, not a typo).
3. **GREEN**: write the minimal code that makes the test pass.
4. **Verify GREEN**: run it. It must pass; other tests must still pass.
5. **REFLECT**: ask if a wrong implementation could pass the test. If yes, the test is too weak — rewrite it before the next cycle.
6. **REFACTOR**: clean up once the test is honest. Keep tests green.

Skipping a step, writing code first, or letting a test pass immediately means the cycle is broken. Delete the code and start over.

## Decision logic: which approach when

| Situation | Use | Why |
|---|---|---|
| Starting a new feature, interface shape unclear | **Seams-first** | Agree on WHERE to test before writing any test. Ask: "What's the public interface, and which seams should we test?" |
| Tempted to skip TDD, write code first | **Iron law** | The discipline kicks in: no production code without a failing test first. Delete code written before tests. |
| Doing real implementation | **Both** | Seams decide WHERE, iron law enforces HOW. Agree seams → write failing test at that seam → minimal code → repeat. |
| Refactoring existing code | **Iron law** | Write characterization tests first (test existing behavior), then refactor with tests as safety net. |
| Bug fix | **Both** | Write a failing test reproducing the bug (iron law), at the appropriate seam (seams-first). |
| Throwaway prototype | **Neither (ask user)** | TDD on throwaway code is ceremony. Confirm with user, then skip. |

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Implement fresh from tests. Period.

**Violating the letter of the rules is violating the spirit of the rules.**

## Seams — where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything — agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?"

When the shape of that interface is itself in question — how deep the module is, where the seam belongs, what the interface should expose — use the `codebase-design` skill for the vocabulary.

## Red-Green-Refactor

### RED — Write Failing Test

Write one minimal test showing what should happen.

**Requirements:**
- One behavior
- Clear name (describes behavior, not implementation)
- Real code (no mocks unless unavoidable)
- Expected value derived independently (literal, worked example, spec) — never recomputed the way the code does it

### Verify RED — Watch It Fail

**MANDATORY. Never skip.**

Confirm:
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

**Test passes?** You're testing existing behavior. Fix test.
**Test errors?** Fix error, re-run until it fails correctly.

### GREEN — Minimal Code

Write simplest code to pass the test. Don't add features, refactor other code, or "improve" beyond the test. Don't anticipate future tests or add speculative features.

### Verify GREEN — Watch It Pass

**MANDATORY.**

Confirm:
- Test passes
- Other tests still pass
- Output pristine (no errors, warnings)

**Test fails?** Fix code, not test.
**Other tests fail?** Fix now.

### ANTI-CHEAT — Reflect on the Test

Before refactoring, stop. Could a deliberately wrong implementation pass this test? If yes, the test is a cheater — it will greenlight bugs.

Check:
- Is the expected value derived independently (spec, literal, worked example) and not copied from the implementation?
- If you replaced the implementation with the simplest plausible wrong version, would the test fail?
- Are you testing through the public seam, not a private side channel?
- Does the test fail for the *right* reason when the feature is missing, not because of setup or typo?

**A test that any wrong implementation can pass is worse than no test.** Rewrite it and watch it fail again before moving on.

### REFACTOR — Clean Up (separate from the loop)

After green only:
- Remove duplication
- Improve names
- Extract helpers

Keep tests green. Don't add behavior. Refactoring belongs to the review stage (see `code-review` skill), not the red-green implementation cycle.

### Repeat

Next failing test for next feature. **One slice at a time.** One seam, one test, one minimal implementation per cycle. Each test is a **tracer bullet** that responds to what the last cycle taught you.

## Anti-patterns

- **Implementation-coupled** — mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological** — the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth.
- **Horizontal slicing** — writing all tests first, then all implementation. Bulk tests verify imagined behavior: you test the shape of things rather than user-facing behavior. Work in **vertical slices** instead — one test → one implementation → repeat.
- **Change detector** — a test that can only fail through an intentional decision (constant value, exact message wording, private structure). It fires on redesign and sleeps through bugs. Test the behavior that depends on the decision, not the decision itself.

## Good Tests

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification — "user can checkout with valid cart" tells you exactly what capability exists.

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. "and" in name? Split it. | `test('validates email and domain and whitespace')` |
| **Clear** | Name describes behavior | `test('test1')` |
| **Shows intent** | Demonstrates desired API | Obscures what code should do |

See [writing-good-tests.md](writing-good-tests.md) for the full rules that keep tests honest, [tests.md](tests.md) for good/bad examples, and [mocking.md](mocking.md) for mocking guidelines.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests written after pass immediately — which proves nothing. They may test the wrong thing, test the implementation instead of the behavior, or miss the edge case you forgot. |
| "Tests after achieve same goals" | Tests-after answer "what does this do?"; tests-first answer "what should this do?" Tests written after are biased by the code you already wrote. |
| "Already manually tested" | Manual testing is ad-hoc: no record, no re-run, easy to forget cases under pressure. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. The real choice: rewrite with TDD (high confidence) vs. keep it and bolt tests on after (low confidence). |
| "Keep as reference, write tests first" | You'll adapt it. That's testing after. Delete means delete. |
| "Need to explore first" | Fine. Throw away exploration, start with TDD. |
| "Test hard = design unclear" | Listen to test. Hard to test = hard to use. |
| "TDD will slow me down" | TDD IS the pragmatic path: catches bugs before commit, prevents regressions, lets you refactor without fear. |

## Red Flags — STOP and Start Over

- Code before test
- Test after implementation
- Test passes immediately
- Can't explain why test failed
- Tests added "later"
- Rationalizing "just this once"
- "Keep as reference" or "adapt existing code"
- "This is different because..."
- Test can be passed by a trivially wrong implementation
- Feedback loop not run before moving on

**All of these mean: Delete code. Start over with TDD.**

## Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered
- [ ] Test would fail if a nearby wrong implementation existed
- [ ] Project feedback loop was used in each cycle
- [ ] Seams were agreed with user before testing

Can't check all boxes? You skipped TDD. Start over.

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write wished-for API. Write assertion first. Ask user. |
| Test too complicated | Design too complicated. Simplify interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify design. |

## Debugging Integration

Bug found? Write failing test reproducing it. Follow TDD cycle. Test proves fix and prevents regression. Never fix bugs without a test.

## Final Rule

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions without your human partner's permission.

## Feedback Loops Are the Quality Ceiling

The fastest, most reliable feedback loop in the project (typecheck, lint, test, audit, review) sets the upper bound on code quality. AI cannot write better code than the loops that catch its mistakes.

Before you start a TDD cycle:
- Identify the project's primary feedback loop (e.g. `npm test`, `pytest`, `cargo test`, `mix test`, `go test ./...`).
- Run it on the failing test after RED and after GREEN. A failing typecheck or lint is red feedback — fix it before the next test.
- If the project has no fast feedback loop, add one before committing.

If a test cannot be run in the project's feedback loop, it is not a real test. If the loop is too slow, make the next slice smaller.

## Cross-skills

- Invoke `review-cadence` before choosing seams if you're unsure how much upfront design this task needs.
- Invoke `effort-calibration` if the task is trivial or unusually hard, so you don't over- or under-think the TDD loop.
- Invoke `verification-before-completion` to prove each RED/GREEN step with fresh command output before claiming the cycle is complete.
