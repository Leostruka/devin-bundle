---
name: forensic-debugging
description: Use when a bug, algorithm failure, or intermittent defect resists normal debugging, when an audit-grade trail of every hypothesis and experiment is required, or when the user asks for millimetric traceability to localize any failure fast. Extends `debugging` with a mandatory trace ledger, invariant map, and falsification protocol.
triggers: [user, model]
---

# Forensic Debugging

Millimetric traceability: every step produces a durable artifact, so any
algorithm failure is found by following evidence, never by intuition. The
ledger is the state of the investigation; memory is not.

This is the escalation-tier protocol over `skills/debugging`. Use it when
the failure is algorithmic, intermittent, silent-corrupting, or has already
survived one ordinary debugging pass.

## Non-negotiables

- No fix before root cause. A symptom patch is a failed investigation.
- Every hypothesis is falsifiable. If an experiment cannot refute it, it is
  not an experiment.
- Every experiment is logged BEFORE it runs: prediction first, observation
  after. Post-hoc rationalization is contamination.
- Never deduce what a tool can measure. A guess with confidence is still a
  guess; instrument it.
- The ledger must let a fresh agent reconstruct the full state in under
  two minutes: what was tried, what was ruled out, the current best
  hypothesis, and the next planned experiment.

## The Trace Ledger (mandatory)

Create `<scratch>/debug-<slug>.md` (per-project scratch area) at start.
Template: `reference/trace-ledger-template.md`. ID system:

- `I#` invariants the algorithm must preserve
- `P#` probe points placed in code or around boundaries
- `H#` hypotheses, each with its falsification experiment
- `E#` experiments, each with predicted vs observed result
- `O#` observations: every anomaly, including ones you cannot yet explain

Status header is always current:
`REPRODUCED -> LOCALIZING -> ISOLATED -> FIX-UNVERIFIED -> VERIFIED`.
Closing requires `VERIFIED` plus a postmortem line: root cause, fix
commit, regression test.

## Phase 0: Reproduction kernel

- Shrink the trigger to the minimal deterministic repro before anything
  else. Pin seeds, clocks, env vars, input bytes.
- Record exact trigger conditions in the ledger (command, input, env).
- Intermittent failures: quantify the failure rate and the conditions that
  move it (load, timing, ordering) before proceeding. A bug you cannot
  trigger on demand is an instrumentation problem first.

## Phase 1: Invariant map

Enumerate what must be true, as checkable `I#` entries:

- Pre-conditions: input shape, domain, encoding, ordering.
- Per-stage post-conditions: what each stage must output/preserve.
- Conservation laws: counts, sums, bytes in = bytes out, monotonicity.
- Structural invariants: indices in range, no duplicates, sorted, balanced.

A failure is always the FIRST violated invariant. The job: find the last
program point where every `I#` held and the first where one broke.

## Phase 2: Hypothesis table

Before experimenting, enumerate `H#` rows:

| H# | Claim | Falsification experiment | Expected signal if true |
|----|-------|--------------------------|-------------------------|

Cover the space: data-dependent, order-dependent, state-dependent,
environment-dependent, timing-dependent, and "my assumption about X is
wrong". An unexplained anomaly in `O#` must map to some `H#` or spawn one.

## Phase 3: Three-axis bisection

- Code: `git bisect` or staged revert across the suspect range.
- Input: ddmin-style shrink. Halve the input while failure persists;
  recurse on the minimal failing fragment.
- Execution: place probes `P#` at stage boundaries. Binary-search the
  pipeline for the first stage emitting corrupt state, then descend
  inside it (per-line, per-iteration, per-op tracing).

## Phase 4: Probe lattice

Instrument deliberately, mapped in the ledger:

- `P#` at every stage boundary: assert the `I#` expected at that point.
- State dumps at the first-corrupt stage's internals.
- Assertions encode invariants, not vague sanity: `assert len(out) ==
  len(inp)` beats "print something looks off".
- Trace IDs join every probe emission back to `P#` and `E#` in the ledger.
- After the fix: remove ad-hoc probes or gate them behind a flag; keep
  the ones that became regression assertions.

## Phase 5: Root cause proof

A candidate root cause must explain EVERY `O#`, including anomalies set
aside earlier. Requirements:

1. Write the causal chain: input -> defect mechanism -> observed symptom.
2. Falsify the root cause itself: predict behavior under a NEW input the
   experiment has not tried, then verify. A cause that cannot predict is
   not proven.
3. If any `O#` is unexplained, the cause is incomplete: new `H#`, keep
   going.

## Phase 6: Fix and close

- Smallest fix at the mechanism, not the symptom.
- Regression test: the Phase-0 repro kernel becomes a permanent test,
  named after the failure (`edge-coverage` owns the test-side rules).
- Close ledger: postmortem line (root cause, fix ref, test ref).

## Escalation protocol

After 5 experiments without narrowing:

- Raise instrumentation level: more probes, finer granularity, not more
  guesses.
- Swap axis: bisecting code -> bisect input -> differential vs a
  known-good oracle.
- Delegate `debugger` or `researcher` profile WITH the ledger attached;
  the ledger is the handoff.

## Failure-class playbook

| Class | First move |
|-------|------------|
| Nondeterministic | Pin seed/clock; replay log capture; run repro 10x |
| Floating point | Exact-vs-tolerance trace; isolate the first divergent op |
| Concurrency | Interleaving capture; deterministic scheduler; shrink to 2 threads/ops |
| Off-by-one / boundary | Trace indices at loop edges; test n-1, n, n+1 probes |
| Silent corruption | Dual-run vs reference oracle; first-divergence wins |
| Wrong result, no crash | Invariant map FIRST; the missing `I#` is the bug |

## Anti-patterns (instant fails)

- Shotgun logging everywhere: probes without `P#` mapping are noise.
- Experimenting without a logged prediction.
- "It works now" without a falsified root cause.
- Editing code and re-running the repro in the same step.
- Ledger entries written from memory at the end.
