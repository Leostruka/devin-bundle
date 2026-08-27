---
name: diagnosing-bugs
description: Use when the user says 'diagnose', 'debug this', reports something broken, throwing, failing, or slow, or when encountering a bug, test failure, or unexpected behavior and a fix is not yet obvious.
agent: debugger
---
# Diagnosing Bugs (Unified)

A discipline for hard bugs. Skip phases only when explicitly justified.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom
fixes are failure. **Violating the letter of this process is violating the
spirit of debugging.**

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

When exploring the codebase, read `.devin/CONTEXT.md` (if it exists) to get a clear
mental model of the relevant modules, and check `.devin/adr/` in the area you're
touching. If the bug spans multiple files, modules, or a data flow you cannot trace in one pass, invoke `deep-mode` before Phase 1.

## Redact

Show commands, outputs and captured artifacts. **Redact every secret first**
— write `<REDACTED>` in its place. Build loops against env vars, so the
credential stays in the environment rather than in what you show. Captured
artifacts carry auth headers: quote only the lines that carry the signal.

If the redacted output is not enough to diagnose the bug, say so and ask.

## The Iron Law

If you haven't completed Phase 1, you cannot propose fixes.

**Red flags — STOP and return to Phase 1:**
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "It's probably X, let me fix that"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals new problem in different place**

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a **tight**
pass/fail signal for the bug — one that goes red on _this_ bug — you will find
the cause; bisection, hypothesis-testing, and instrumentation all just
consume it. If you don't have one, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to
give up.**

### 1. Read error messages carefully

- Don't skip past errors or warnings. They often contain the exact solution.
- Read stack traces completely. Note line numbers, file paths, error codes.

### 2. Construct a feedback loop — try in roughly this order

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffing stdout against known-good.
4. **Headless browser script** (Playwright / Puppeteer) — drives the UI.
5. **Replay a captured trace.** Save a real network request / payload / event
   log to disk; replay it through the code path in isolation.
6. **Throwaway harness.** Spin up a minimal subset (one service, mocked deps).
7. **Property / fuzz loop.** If "sometimes wrong output", run 1000 random
   inputs and look for the failure mode.
8. **Bisection harness.** If the bug appeared between two known states,
   automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Run same input through old vs new version, diff.
10. **HITL script.** Last resort. Drive the human with
    `scripts/hitl-loop.template.py` so the loop is still structured.

Build the right feedback loop, and the bug is 90% fixed.

### 3. Check recent changes

- What changed that could cause this? Git diff, recent commits.
- New dependencies, config changes, environmental differences.

### 4. Gather evidence in multi-component systems

**WHEN system has multiple components (CI → build → signing, API → service →
database):**

```
For EACH component boundary:
  - Log what data enters component
  - Log what data exits component
  - Verify environment/config propagation
  - Check state at each layer

Run once to gather evidence showing WHERE it breaks
THEN analyze evidence to identify failing component
THEN investigate that specific component
```

### 5. Trace data flow

**WHEN error is deep in call stack:**

- Where does bad value originate?
- What called this with bad value?
- Keep tracing up until you find the source.
- Fix at source, not at symptom.

See `root-cause-tracing.md` in this directory for the complete
backward tracing technique.

### Tighten the loop

Treat the loop as a product. Once you have _a_ loop, **tighten** it:

- Can I make it faster? (Cache setup, skip unrelated init, narrow scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it more deterministic? (Pin time, seed RNG, isolate filesystem.)

A 30-second flaky loop is barely better than no loop; a 2-second deterministic
one is tight — a debugging superpower.

### Non-deterministic bugs

The goal is not a clean repro but a **higher reproduction rate**. Loop the
trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps.
A 50%-flake bug is debuggable; 1% is not — keep raising the rate.

### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) access
to whatever environment reproduces it, (b) a redacted captured artifact (HAR
file, log dump, core dump, screen recording with timestamps), or (c)
permission to add temporary production instrumentation. Do **not** proceed to
hypothesise without a loop.

### Completion criterion — a tight loop that goes red

Phase 1 is done when the loop is **tight** and **red-capable**: you can name
**one command** — a script path, a test invocation, a curl — that you have
**already run at least once** (show the invocation and its output, redacted),
and that is:

- [ ] **Red-capable** — drives the actual bug code path and asserts the
      **user's exact symptom**, so it can go red on this bug and green once
      fixed. Not "runs without erroring" — it must be able to _catch this
      specific bug_.
- [ ] **Deterministic** — same verdict every run (flaky bugs: high repro rate).
- [ ] **Fast** — seconds, not minutes.
- [ ] **Agent-runnable** — you can run it unattended; human only via
      `scripts/hitl-loop.template.py`.

If you catch yourself reading code to build a theory before this command
exists, **stop — jumping straight to a hypothesis is the exact failure this
skill prevents.** No red-capable command, no Phase 2.

## Phase 2 — Reproduce + minimise + pattern analysis

Run the loop. Watch it go red — the bug appears.

Confirm:

- [ ] The loop produces the failure mode the **user** described — not a
      different failure nearby. Wrong bug = wrong fix.
- [ ] The failure is reproducible across multiple runs (or at high enough rate).
- [ ] You have captured the exact symptom (error message, wrong output, slow
      timing) so later phases can verify the fix.

### Minimise

Once it's red, shrink the repro to the **smallest scenario that still goes
red**. Cut inputs, callers, config, data, and steps **one at a time**,
re-running the loop after each cut — keep only what's load-bearing.

Done when **every remaining element is load-bearing** — removing any one makes
the loop go green.

### Pattern analysis

1. **Find working examples** — locate similar working code in same codebase.
2. **Compare against references** — read reference implementation COMPLETELY.
   Don't skim. Understand the pattern fully before applying.
3. **Identify differences** — list every difference, however small. Don't
   assume "that can't matter".
4. **Understand dependencies** — what components, settings, config, env, assumptions.

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any of them. Single-
hypothesis generation anchors on the first plausible idea.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear
> / <changing Z> will make it worse."

If you cannot state the prediction, the hypothesis is a vibe — discard or
sharpen it.

**Show the ranked list to the user before testing.** They often have domain
knowledge that re-ranks instantly ("we just deployed a change to #3"), or know
hypotheses they've already ruled out. Don't block on it — proceed with your
ranking if the user is AFK.

## Phase 4 — Instrument

Each probe must map to a specific prediction from Phase 3. **Change one
variable at a time.**

Tool preference:

1. **Debugger / REPL inspection** if the env supports it. One breakpoint
   beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at
the end becomes a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions, logs are usually wrong. Instead:
establish a baseline measurement (timing harness, `performance.now()`,
profiler, query plan), then bisect. Measure first, fix second.

## Phase 5 — Fix + regression test

Write the regression test **before the fix** — but only if there is a
**correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it
occurs at the call site. If the only available seam is too shallow (single-
caller test when the bug needs multiple callers, unit test that can't
replicate the chain), a regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it. The
codebase architecture is preventing the bug from being locked down. Flag this
for the next phase.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam. Watch it fail.
2. Apply the fix. **ONE change at a time.** No "while I'm here" improvements.
3. Watch it pass. Re-run the Phase 1 feedback loop against the original
   (un-minimised) scenario.
4. No other tests broken? Issue actually resolved?

### If fix doesn't work

- **< 3 attempts:** Return to Phase 1, re-analyze with new information. Form
  NEW hypothesis. DON'T add more fixes on top.
- **≥ 3 attempts:** STOP. Question the architecture (see below).

### If 3+ fixes failed: question architecture

**Pattern indicating architectural problem:**
- Each fix reveals new shared state/coupling/problem in different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor architecture vs. continue fixing symptoms?

**Discuss with user before attempting more fixes.** This is NOT a failed
hypothesis — this is a wrong architecture.

## Phase 6 — Cleanup + post-mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or absence of seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix)
- [ ] Throwaway prototypes deleted (or moved to clearly-marked debug location)
- [ ] The hypothesis that turned out correct is stated in the commit / PR
      message — so the next debugger learns

**Then ask: what would have prevented this bug?** If the answer involves
architectural change (no good test seam, tangled callers, hidden coupling)
hand off to `improve-codebase-architecture` with the specifics. Make the
recommendation **after** the fix is in, not before.

## Stopping Criterion (VRR-Stop)

If after 2+ repair rounds the true validity decreases (not just the proxy),
stop and escalate. Don't keep repairing if each round makes it worse.

**Signs you should stop:**
- Each fix introduces new failures
- Test count goes up but pass rate goes down
- The fix addresses a symptom but creates a new one elsewhere
- You've applied 3+ fixes to the same function without convergence

**What to do instead:**
1. Stop fixing. Revert to last known-good state.
2. Re-read the original error with fresh eyes.
3. Consider that the approach is wrong, not the implementation.
4. Escalate: "I've attempted N fixes. Each made it worse. The root cause may
   be architectural, not implementation-level."

**Source:** VRR-Stop (arXiv:2607.17641). 60.6pp improvement over fixed
five-round repair.

## When Process Reveals "No Root Cause"

If systematic investigation reveals issue is truly environmental,
timing-dependent, or external:

1. You've completed the process.
2. Document what you investigated.
3. Implement appropriate handling (retry, timeout, error message).
4. Add monitoring/logging for future investigation.

**But:** 95% of "no root cause" cases are incomplete investigation.

## Interaction-Centric Failure Dimension

Beyond "what" (bug type), identify "where" — which component interaction
failed. 41 failure modes mapped to component edges with Cohen's κ=0.76
(arXiv:2607.28802).

| Edge | Common failure modes |
|---|---|
| Model → Tool | Hallucinated arguments, wrong tool selection, invalid syntax |
| Model → Memory | Stale context, forgotten constraints (Governance Decay), wrong retrieval |
| Tool → Tool | Output format mismatch, missing dependency, timeout cascade |
| Agent → Environment | Permission denied, file not found, network unreachable |

When diagnosing, classify on both dimensions:
1. **What** — the failure type (syntax, logic, timeout, permission, etc.)
2. **Where** — the component edge that failed

If multiple bugs cluster on the same edge, the architecture at that edge needs
improvement, not just the individual bug fixes.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question pattern, don't fix again. |

## Supporting Techniques

Available in this directory:

- **`root-cause-tracing.md`** — Trace bugs backward through call stack
- **`defense-in-depth.md`** — Add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** — Replace arbitrary timeouts with condition polling
