---
name: performance
description: Use when the user wants to profile, optimize, load-test, or measure the performance of code, queries, or infrastructure.
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

## Load-test + DB tuning playbook

The "real project" loop (compose -> load -> measure -> tune):

1. **Reproduce deps with docker-compose.** Every project should ship
   a Dockerfile plus a compose for dependencies (db, cache, proxy).
   Run app and db as separate services; prefer Docker on Linux - on
   Mac/Windows the daemon runs in a VM and distorts measurements.
2. **Isolate network bottlenecks.** `network_mode: host` in compose
   removes Docker bridge NAT overhead; if latency changes under host
   mode, the bottleneck was the network, not the app.
3. **Generate real load.** Gatling (Scala simulation, HTML report)
   or Vegeta (CLI, `attack | report`) against the real endpoint.
   Measure p50/p95/p99 and throughput, never the mean.
4. **Check whether the db is the bottleneck.** `EXPLAIN ANALYZE` on
   the slow query shows real per-plan cost (seq scan vs index).
   Full-text search: compare `LIKE '%x%'` vs `tsvector` before
   swapping databases.
5. **Size the connection pool.** Watch `pg_stat_activity` (pgAdmin)
   under load: a pool larger than connections actually used is waste;
   a wait queue means the pool is too small. Starting formula:
   `pool = (cores * 2) + spindle_count`.
6. **Threads vs fibers.** Language/IO model changes how many
   connections and how much RAM each worker needs; tune pool and
   limits together.

## See also

- `debugging` — failure and root-cause analysis.
- `performance` — speed, throughput, and resource optimization.

## Output rule

- Report metric, before, after, and the tool/command used.
- Prefer repeatable benchmark scripts over one-off manual checks.
