---
name: code-review
description: "Review code changes against two axes — Standards (does the code follow documented conventions + code smell baseline?) and Spec (does the code match what was asked for?). Dispatches parallel sub-agents to preserve context. Use when completing tasks, reviewing a branch/PR, before merging, or when the user asks to 'review since X'. Merges the subagent-dispatch workflow with the two-axis review methodology."
---

# Code Review (Unified)

Two traditions, one review. This skill merges the **subagent-dispatch workflow** (review early, review often, preserve coordinator context) with the **two-axis methodology** (Standards vs Spec, parallel sub-agents, code smell baseline).

## Decision logic: which approach when

| Situation | Use | Why |
|---|---|---|
| You're the coordinator, just finished a task | **Subagent dispatch** | Don't burn your context window reviewing inline. Dispatch a reviewer subagent; only findings come back. |
| Reviewing a branch/PR against a spec | **Two-axis** | Standards and Spec are deliberately separate axes — one can pass while the other fails. Report them side by side. |
| Real review before merge | **Both** | Dispatch a subagent (preserve context) that runs the two-axis review (thorough methodology). |
| Quick check during development | **Subagent dispatch** | Fresh perspective when stuck, baseline check before refactoring. |
| No spec available | **Standards axis only** | Skip Spec sub-agent, note "no spec available" in report. |
| Reviewing your own work mid-task | **Subagent dispatch** | You're too close to the code. A subagent with precisely crafted context sees it fresh. |

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## The Two Axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. If they didn't specify one, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, etc.)
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user. If they say there isn't one, the **Spec** sub-agent will skip.

### 3. Identify the standards sources

Anything in the repo that documents how code should be written: `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `AGENTS.md`, etc.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** — a fixed set of Fowler code smells that applies even when a repo documents nothing:

- **Mysterious Name** — name doesn't reveal what it does. → rename.
- **Duplicated Code** — same logic shape in multiple places. → extract shared shape.
- **Feature Envy** — method reaches into another object's data more than its own. → move the method.
- **Data Clumps** — same few fields travel together. → bundle into one type.
- **Primitive Obsession** — primitive standing in for a domain concept. → give it its own type.
- **Repeated Switches** — same switch/if-cascade recurs. → replace with polymorphism or shared map.
- **Shotgun Surgery** — one change forces scattered edits. → gather what changes together.
- **Divergent Change** — one module edited for unrelated reasons. → split by reason.
- **Speculative Generality** — abstraction for needs the spec doesn't have. → delete it.
- **Message Chains** — long `a.b().c().d()` navigation. → hide behind one method.
- **Middle Man** — class that mostly delegates. → cut it, call direct.
- **Refused Bequest** — subclass that ignores most of what it inherits. → drop inheritance, use composition.

**Two rules bind the smell baseline:**
- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic, never a hard violation. Skip anything tooling already enforces.

### 4. Dispatch review sub-agent(s)

**Option A: Single sub-agent (lighter weight)**

Dispatch a `general-purpose` subagent using the template at [code-reviewer.md](code-reviewer.md), enhanced with the two-axis methodology. Fill placeholders:
- `{DESCRIPTION}` — brief summary of what was built
- `{PLAN_OR_REQUIREMENTS}` — what it should do (spec path, issue text, or requirements)
- `{BASE_SHA}` — starting commit
- `{HEAD_SHA}` — ending commit

**Option B: Parallel sub-agents (thorough)**

Spawn both sub-agents in parallel so they don't pollute each other's context:

**Standards sub-agent prompt** — include:
- The full diff command and commit list.
- The list of standards-source files, plus the smell baseline pasted in full.
- The brief: "Report — per file/hunk — (a) every place the diff violates a documented standard: cite the standard; and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** — include:
- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings — the two axes are deliberately separate.

End with a one-line summary: total findings per axis, and the worst issue within each axis. Don't pick a single winner across axes.

### 6. Act on feedback

- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with technical reasoning, code/tests that prove it)

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just review the diff myself" | You're the coordinator — reviewing inline burns the context window you need to keep driving the work. Dispatch a subagent. |
| "The reviewer needs my whole session history" | Hand it precisely crafted context, never your session's history. Keeps the reviewer on the work product, not your thought process. |
| "It's simple, skip review" | Simple code breaks. Review takes 2 minutes. |
| "I already manually checked" | Manual review is ad-hoc: no record, no re-run, easy to miss things under pressure. |

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback
- Say "looks good" without actually reading the diff
- Mark nitpicks as Critical
- Give feedback on code you didn't read

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: [code-reviewer.md](code-reviewer.md)
