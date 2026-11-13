---
name: edge-coverage
description: Use when assembling or auditing a test suite for rigorous edge-case coverage, when the user asks for meticulous test construction rules, boundary/equivalence analysis, or a completeness standard before a suite may be called done. Extends `testing`, `tdd`, `edge-cases`, and `mutation-testing` with a mandatory Edge Inventory that drives the suite.
triggers: [user, model]
---

# Edge Coverage

Meticulous test assembly: the suite is derived from an explicit edge
inventory, not from intuition. Completeness is measured as inventory
coverage, never as a feeling.

This is the construction standard over `skills/testing`, `skills/tdd`,
`skills/edge-cases`, and `skills/mutation-testing`. Use it when building
a suite from scratch, auditing an existing one, or when "is it tested?"
must have a defensible answer.

## The contract

- No test code before the Edge Inventory. The inventory is written first,
  reviewed, and only then implemented.
- Every inventory row maps to >= 1 named test. Every test maps back to
  >= 1 inventory row. Orphans in either direction are defects.
- Every test must be able to fail: it kills a named mutant or asserts a
  distinct behavior. Decorative tests are deleted.
- Nondeterministic tests are defects: seeds pinned, clocks frozen, order
  independent.

## Step 1: Input space decomposition

Enumerate equivalence classes, then attack every boundary.

**Classes:** valid / invalid-type / invalid-format / out-of-domain /
degenerate (empty, null, zero, single-element, max-size).

**Numeric boundaries:** for every bound `b`, test `b-1`, `b`, `b+1`.
Lengths: `0, 1, n-1, n, n+1`. Signed: `-1, 0, +1, MIN, MAX`,
overflow `MAX+1`, underflow `MIN-1`.

**Structural edges:** empty collection, single element, duplicates,
sorted, reverse-sorted, all-identical, alternating, nesting depth
0/1/max, cyclic references where legal.

**Encoding edges:** empty string, ASCII, accents, emoji/astral plane,
malformed UTF-8, overlong sequences, CRLF vs LF, BOM, embedded NUL,
max-length vs max-length+1.

**Temporal edges:** epoch, leap day, DST transition, year boundaries,
far-past/far-future, timezone offsets, sub-second granularity, negative
durations.

**Format edges:** trailing whitespace, missing/extra delimiters, deep
nesting, case sensitivity, locale-dependent decimal/grouping separators.

## Step 2: State and transition coverage

- Every reachable state: initial, each intermediate, terminal, error.
- Every transition: legal plus ILLEGAL (must reject, not corrupt).
- Re-entry: call it twice, call it after failure, call it after success.
- Cancellation mid-transition; resume from partial completion.
- Idempotent operations applied 2x and 3x: same result.
- Orderings: reversed event order, duplicated events, missing events.

## Step 3: Combinatorics

- Small spaces: full enumeration.
- Parameter interactions: pairwise coverage minimum; explicitly test the
  pairs most likely to interact (flag x state, size x type, mode x input
  shape).
- Feature flags: each flag x each affected path; flag-on + flag-off.

## Step 4: Error-path matrix

Every error branch gets a test that triggers it:

| Error branch | Trigger input | Asserted |
|--------------|---------------|----------|
| each throw/raise/return-err | the input that forces it | error type + payload fields |
| timeout path | clock/latency control | timeout + cleanup state |
| retry path | transient failure injection | retry count + final state |
| cancel path | cancel signal mid-op | no partial mutation visible |

Assert error TYPE and payload, never a bare "it raised". After every
error test, assert post-error state: nothing half-written, resources
released, invariants intact.

## Step 5: Concurrency and resource edges

- Races: submit the same op twice concurrently; shared counter under N
  writers; TOCTOU on every check-then-act.
- Interleavings: pause mid-operation (barrier/sleep injection), resume.
- Cancellation while blocked on I/O.
- Backpressure: producer faster than consumer, bounded queue full.
- Resource limits: buffer at N and N+1, file handles near limit, memory
  ceiling, disk full, connection pool exhausted.
- Async: out-of-order completion, partial results, late events after
  close.

## Step 6: Oracle discipline

In order of preference:

1. Expected output: golden files, spec examples.
2. Reference oracle: stdlib, known-good implementation, brute force on
   small inputs.
3. Property oracles when no expected output exists:
   round-trip (`decode(encode(x)) == x`), idempotence (`f(f(x)) == f(x)`),
   monotonicity, conservation (sum/count/bytes preserved), invariant
   assertions after every op.
4. Metamorphic relations: perturb input -> output changes predictably
   (sort stays sorted under permutation; doubling input doubles the
   count).
5. Self-consistency: internal invariants across the whole run.

A test with no oracle is a smell; note it in the inventory as
`oracle: none` and justify or strengthen.

## Step 7: Test anatomy

- Name: `test_<unit>_<condition>_<expected>` so the inventory row is
  recoverable from the name alone.
- Arrange / act / assert, single concept per test, one logical
  assertion (multiple physical asserts about the SAME result are fine).
- Independence: any order, any subset, parallel-safe.
- Determinism: seeded randoms, frozen clock, no wall-time sleeps where
  a control exists, no network unless the test IS the network contract.
- Fast: the suite's value decays with runtime; slow tests get marked and
  separated, not deleted.

## Step 8: Coverage accounting

- Branch > line > function. Report per-module, not one global number.
- Mutation score is the real gate (`skills/mutation-testing`): surviving
  mutants map to missing inventory rows.
- Every new branch in a diff requires an inventory row and a test.
- The deliverable report is coverage BY INVENTORY: rows total, rows
  covered, rows deliberately skipped (with reason), mutants survived.

## Step 9: Regression discipline

- Every bug gets a reproducing test BEFORE the fix (`forensic-debugging`
  produces the repro kernel; it becomes a permanent test here).
- Postmortems feed the inventory: each incident class becomes a
  checklist row so the same edge family is never missed twice.
- Never delete a failing test: fix the code or fix the oracle, and
  record the decision.

## Step 10: Final gate checklist

- [ ] Inventory written and reviewed BEFORE tests.
- [ ] Every row has a test; every test has a row.
- [ ] Every branch in the diff covered.
- [ ] Every test can fail (asserts something real).
- [ ] Zero nondeterminism sources unaccounted for.
- [ ] Error paths asserted for type + payload + post-state.
- [ ] Surviving mutants reviewed and either killed or justified.
- [ ] Oracles assigned; `oracle: none` rows justified.

## Reference

`reference/edge-inventory-template.md`: the mandatory inventory schema.
