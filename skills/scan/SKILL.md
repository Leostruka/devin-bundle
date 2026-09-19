---
name: scan
description: Use when the user wants a goal-driven, codebase-wide investigation — "scan for dead code", "find N+1 queries", "check test coverage gaps", "audit style/migration compliance". Replicates Devin Cloud's /scan (Code Scans): Plan → Shard → Map → Reduce, parallel read-only subagents, prioritized findings report with evidence.
triggers: [user, model]
---

# Scan — goal-driven codebase investigation

Local equivalent of Devin Cloud `/scan` (Code Scans). Turns a broad
engineering goal into a scoped investigation, fans out parallel read-only
subagents over repo shards, then reduces findings into a prioritized report.

Non-goals: no auto-fixes (remediation is a separate, gated step), no ticket
creation without approval, no security exploit work (see `security` skill).

## Workflow — Agentic MapReduce

### 1. Plan (scope + criteria)

Extract or ask (`ask_user_question`, ≤2 rounds) for:

- **Goal**: what to investigate (e.g. "unused exports", "N+1 queries").
- **Scope**: dirs/globs in or out (default: whole repo minus vendored/generated).
- **Criteria**: what counts as a finding + severity rubric.
- **Size cap**: shard count and report limits (defaults below).

Record the scan spec at `.devin/scans/<YYYY-MM-DD>-<slug>.spec.md`
(one short file: goal, scope, criteria, shard list, timestamp).

### 2. Shard

Split the in-scope surface into **4–8 shards** (never more than 8 — context
and token budget). Shard by top-level dir, module, or glob cluster. Each
shard must be describable as a path set + short focus line. Prefer
`find_file_by_name`/manifest boundaries over arbitrary splits.

### 3. Map (parallel read-only subagents)

Dispatch **one `researcher` (or `subagent_explore`) background subagent per
shard** — all in parallel, disjoint read sets. Each prompt must be
self-contained (subagents see no session context):

- The goal + criteria verbatim.
- Its shard paths.
- Output contract: findings only, each as
  `file:line | severity (high/med/low) | evidence (≤1 line quote) | why it
  matches criteria`. Max 15 findings per shard. No findings → say so.
- Explicitly: **read-only, no edits, no fixes proposed beyond one line.**

Wait for all (`read_subagent block=true` or completion notifications).

### 4. Reduce (dedupe + prioritize + report)

- Dedupe on `file:line` ±2 lines; merge same-pattern findings.
- Rank: severity first, then frequency, then blast radius.
- Write `.devin/scans/<YYYY-MM-DD>-<slug>.md` (report template below).
- Print a ≤12-line summary to the user: counts by severity + top 5.

### 5. Remediate (opt-in only)

Never fix during a scan. Offer next steps: pick findings →
`planning`/`execution` flow → `implementer` subagents with tests. For bulk
identical fixes, dispatch sequentially, one at a time.

## Report template

```markdown
# Scan — <goal>
Date: <YYYY-MM-DD> | Shards: N | Findings: M

## Top findings (by severity)
| # | file:line | severity | evidence | note |

## All findings (grouped by shard/pattern)
...

## Coverage notes
- shards skipped / files unreadable / criteria edge cases
```

## Guardrails

- Subagents are read-only; the scan itself never edits repo code.
- Every finding carries `file:line` evidence — drop unverifiable claims.
- Cap the report at 100 findings; group the rest by pattern.
- Secrets found → report the location class only, never the value (Rule 19).
- Cost: ~1 subagent per shard; keep ≤8 unless the user asks for more.

## Examples

- `/scan dead code` → criteria: unreferenced exports/functions; shards by
  src dir; report ranks by confidence.
- `/scan test gaps` → map source files without matching test files.
- `/scan style guide` → criteria from an AGENTS.md/style doc shard.
