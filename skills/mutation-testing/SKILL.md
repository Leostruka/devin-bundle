---
name: mutation-testing
description: Use when the user asks to find testing gaps, mutation test, or identify surviving mutants.
---
# Mutation Testing

Perform mutation testing on the current codebase to find gaps in test coverage.

## Goal

A **mutation** is a small, deliberate change to production code that mimics a realistic bug a human might introduce. A **mutant** is the resulting modified codebase. If the test suite catches the bug (tests fail), the mutant is **killed**. If tests still pass, the mutant **survives** — exposing a gap in test coverage.

The objective is to find as many surviving mutants as possible, prioritised by risk.

## Prerequisites

This skill expects a local clone of a VCS project. If that is not the case, stop and explain why.

Before any testing, ensure local dependencies are running (`docker compose up -d` or equivalent). On compose failure, check whether containers from another project are occupying ports and kill them.

## What to Mutate

### Priority targets (highest to lowest)

1. **Security and auth**: authentication checks, permission gates, encryption, token validation, input sanitisation
2. **Control flow**: condition inversions (`==` ↔ `!=`, `<` ↔ `<=`), removed or inverted `if` branches, swapped `switch`/`case` fall-throughs, early returns removed or added
3. **Validation**: removed or weakened input validation, boundary checks changed, nil/null guard removal
4. **State and values**: variables zeroed or hardcoded, default values changed, constants altered
5. **Error handling**: errors swallowed (replaced with nil/null), retry logic removed, fallback paths deleted

### What NOT to mutate

- Test code, test helpers, fakes, mocks, fixtures, or end-to-end test harnesses
- Logging, tracing, or metrics-only code blocks (unless they also affect control flow)
- Generated code or vendored dependencies

### Bias toward survivors

Focus mutations where test coverage is likely weakest:

- **Tests that test the mock**: mock returns a hardcoded value matching a production default — mutating that default is invisible
- **Model coupling**: tests import production models and assert on fields — exercises serialisation, not behaviour
- **Happy-path-only tests**: multiple branches but only the success path is tested
- **Missing edge cases**: boundary values, empty collections, nil/null inputs, zero-length strings

## Method

### Stage 1 — Discovery

Investigate the codebase and identify candidate mutations. Use subagents to parallelise discovery across packages, modules, or directories — one subagent per logical area.

Each mutation must be assigned a unique sequential number (e.g. `MUT-001`, `MUT-002`, ...).

**Target density**: ~1 mutation per 50 lines of production code. Guideline, not hard rule.

**Time cap**: if no new viable mutation has been identified for 3 minutes, stop and proceed.

For each candidate, record:
- Mutation number
- File path and line number(s)
- Description of the change
- Rationale (why this might survive)

### Stage 2 — Validation (local first, CI optional)

For each candidate mutation:

1. Create a git worktree on a new branch named `mut-<NUMBER>-<short-kebab-description>`.
2. Apply the mutation.
3. Run static analysis: linter, type checks, compilation — use the project's standard tooling. If no local tooling, check CI config for what tools are used and attempt to run locally. **Do not install missing tools without prompting.**
4. Run targeted local tests: tests in the mutated package/module that reference the mutated function or type. Use the race detector where supported. If tests take longer than 1 minute, consider the mutation viable and move on.
5. **If static analysis or tests fail** → mark the mutant as **killed locally**, delete the worktree, move to next candidate.
6. **If the mutant survives local validation** → optionally push the branch and trigger CI for further validation.

**CI-optional path**: If CI is available (GitHub Actions, CircleCI, GitLab CI, etc.), push surviving branches in batches and poll for results. If CI fails → **killed in CI**. If CI passes → **survivor**.

**Local-only path**: If no CI is available or configured, a mutant that survives local validation is already a **survivor** — local tests didn't catch it.

**Cleanup**: after a mutant is killed, remove the worktree promptly.

#### Stage 2 Summary

| # | Mutation | File | Line | Branch | Status |
|---|----------|------|------|--------|--------|
| MUT-001 | Inverted auth check | `pkg/auth/verify.go` | 42 | `mut-001-invert-auth` | Survivor |
| MUT-002 | Removed nil guard | `pkg/api/handler.go` | 118 | `mut-002-rm-nil-guard` | Killed (local) |

### Stage 3 — Production Cross-Reference (optional)

Attempt to determine whether surviving mutants' code paths are exercised in production. Use any available observability tooling — Honeycomb, Datadog, Kibana, Prometheus, New Relic, CloudWatch, or other connected MCP servers/CLIs.

If no observability access is available, note this and skip to Stage 4.

Update the summary table with a **Production Traffic** column: **High**, **Low**, **None found**, or **Unknown**.

### Stage 4 — Risk Assessment

For each survivor, assess overall risk:

- **Severity**: what could go wrong if this bug shipped? (auth bypass > cosmetic issue)
- **Production traffic**: is this code path actually hit?
- **Blast radius**: how many users/systems would be affected?
- **Detectability**: would monitoring/alerting catch this before users notice?

Assign a risk level: **Critical**, **High**, **Medium**, or **Low**.

## Cross-skills

- Use `tdd` when adding tests to kill surviving mutants.
- Use `observability-quality` when production cross-reference needs logs, metrics, or tracing.
- Use `continuous-improvement` to run a 10-step loop when the same test gaps keep appearing.

Present the final summary table sorted by risk (highest first):

| # | Mutation | File | Line | Branch | Prod Traffic | Risk | Rationale |
|---|----------|------|------|--------|-------------|------|-----------|
| MUT-001 | Inverted auth check | `pkg/auth/verify.go` | 42 | [link] | High | Critical | Auth bypass on a hot path, no test coverage |
| MUT-017 | Hardcoded timeout to 0 | `pkg/worker/poll.go` | 89 | [link] | Low | Medium | Tight loop but only in batch worker |
