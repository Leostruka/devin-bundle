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

The "projecto real" loop (compose -> carga -> medir -> ajustar):

1. **Reproduzir deps com docker-compose.** Todo projeto deve ter
   Dockerfile + compose das dependencias (db, cache, proxy). Rode a
   app e o banco como servicos separados; prefira Docker em Linux -
   em Mac/Windows o daemon numa VM distorce medidas.
2. **Isolar gargalos de rede.** `network_mode: host` no compose remove
   o overhead da bridge NAT do Docker; se a latencia muda com host
   mode, o gargalo era rede, nao app.
3. **Gerar carga real.** Gatling (simulacao em Scala, relatorio HTML)
   ou Vegeta (CLI, `attack | report`) batendo no endpoint real.
   Meça p50/p95/p99 e throughput, nao media.
4. **Verificar se o banco e o gargalo.** `EXPLAIN ANALYZE` na query
   lenta mostra custo real por plano (seq scan vs index). Full-text
   search: compare `LIKE '%x%'` vs `tsvector` antes de trocar de db.
5. **Dimensionar pool de conexoes.** Observe `pg_stat_activity`
   (pgAdmin) sob carga: pool maior que conexoes usadas e desperdicio;
   fila de espera = pool pequeno demais. Formula inicial:
   `pool = (cores * 2) + spindle_count`.
6. **Threads vs fibers.** Linguagens/IO model mudam quantas conexoes
   e quanta RAM cada worker precisa; ajuste pool e limits juntos.

## See also

- `debugging` — failure and root-cause analysis.
- `performance` — speed, throughput, and resource optimization.

## Output rule

- Report metric, before, after, and the tool/command used.
- Prefer repeatable benchmark scripts over one-off manual checks.
