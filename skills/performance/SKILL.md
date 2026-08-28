---
name: performance
description: "Use when the user wants to profile, optimize, load-test, or measure the performance of code, queries, or infrastructure."
triggers: [user, model]
---

# Performance

Measure, profile, and optimize speed, throughput, and resource usage.

## When to use

- Code or queries are slow.
- Need load testing before a release.
- High CPU, memory, or latency is reported.
- Want to compare before/after performance.

## Core protocol

1. **Reproduce the scenario.** Gather inputs, endpoints, queries, and expected load.
2. **Measure baseline.** Use built-in timers, APM, or ad-hoc benchmarks.
3. **Profile.** Find hot paths with profilers, query plans, or flame graphs.
4. **Hypothesize and fix.** Target the biggest bottleneck first.
5. **Re-measure.** Confirm improvement with the same workload.
6. **Set guardrails.** Add budgets, alerts, or regression tests.

## See also

- `diagnosing-bugs` — failure and root-cause analysis.
- `performance` — speed, throughput, and resource optimization.

## Output rule

- Report metric, before, after, and the tool/command used.
- Prefer repeatable benchmark scripts over one-off manual checks.
