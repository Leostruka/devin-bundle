---
name: subagent-router
description: Use when deciding whether to dispatch a subagent, which profile to use, and how many concurrent agents to run. Classifies task complexity, selects profile by capability + cost, and applies budget presets.
---
# Subagent Router

The routing layer for subagent dispatch. Answers three questions in order:

1. **Should I dispatch at all?** (early exit)
2. **Which profile?** (capability + cost match)
3. **How deep?** (budget preset)

This skill does NOT replace `dispatching-parallel-agents` (parallel vs sequential),
`subagent-driven-development` (per-task workflow), or `tool-and-skill-discovery`
(skill selection). It sits ABOVE them — it classifies the task and delegates to
the right skill for execution.

## When to Use

- Before any non-trivial task that could benefit from subagent dispatch
- When unsure which profile to use for a task
- When deciding whether to handle inline or delegate
- When multiple profiles could match and you need to pick by cost + capability

## When NOT to Use

- Task is obviously simple (typo, single-line fix) — just do it
- Task is obviously complex with a known workflow (SDD plan execution) — use
  `subagent-driven-development` directly
- You already know the profile and preset — skip classification

## The Routing Decision

### Step 1: Classify complexity (early exit)

```
SIMPLE   → handle inline, no dispatch
MEDIUM   → single subagent dispatch
COMPLEX  → multi-agent sequence (researcher → architect → implementer → reviewer)
PARALLEL → multiple independent subagents in parallel (dispatching-parallel-agents)
```

**Simple signals:**
- Single file, <50 lines of change
- Clear path, no research needed
- You can describe the change in one sentence and know the exact file
- Mechanical fix (typo, missing import, rename)

**Medium signals:**
- Multiple files but scoped, needs some investigation
- Clear requirements, bounded implementation
- Single subsystem, no cross-cutting concerns

**Complex signals:**
- Multi-system, needs research + design + implementation
- Architectural decisions with long-term impact
- Unfamiliar domain requiring investigation first
- Security, performance, or data integrity at stake

**Parallel signals:**
- 2+ independent failures (different test files, different subsystems)
- No shared state between investigations
- Each problem can be understood without context from others

### Step 2: Select profile (capability + cost)

| Task need | Profile | Model | Cost tier |
|---|---|---|---|
| Codebase reconnaissance, doc lookup, web research | `researcher` | SWE-1.6 | $ |
| Code review, spec compliance, verification | `reviewer` | sonnet | $$ |
| Bounded implementation from spec | `implementer` | parent | $$$ |
| Architecture, trade-offs, deep module design | `architect` | sonnet | $$ |
| Systematic debugging, root cause analysis | `debugger` | parent | $$$ |
| Read-only exploration (built-in) | `subagent_explore` | SWE-1.6 | $ |
| General-purpose with full tools (built-in) | `subagent_general` | parent | $$$ |

**Selection rules:**

1. Match by capability first — what does the task NEED?
2. When two profiles match, pick the cheaper one
3. When no custom profile fits, use `subagent_explore` (read-only) or
   `subagent_general` (full tools)
4. When task needs more capability than profile's default model, switch
   parent session model with `/model <model>` before dispatching

**Anti-pattern: don't use `implementer` for research.** `researcher` is 10x
cheaper and read-only. Don't use `architect` for a typo fix — handle inline.

### Step 3: Apply budget preset

| Preset | Reviewers | Repair loops | Independent reflection | When |
|---|---|---|---|---|
| **economy** | 0-1 | 1 | No | Routine refactoring, docs, low-risk tests |
| **standard** | up to 2 | 2 | On critical changes | Default — most implementation tasks |
| **strict** | up to 3 | 3 | Always | Security, core logic, public API, unfamiliar domain |

Select by task RISK, not size. A 20-line auth change is strict. A 500-line
doc update is economy.

### Step 4: Dispatch

Hand off to the execution skill:

- **SIMPLE** → handle inline (no skill needed)
- **MEDIUM** → `run_subagent` with selected profile + brief
- **COMPLEX** → sequence: `researcher` → `architect` → `implementer` → `reviewer`
  (use `subagent-driven-development` if you have a multi-task plan)
- **PARALLEL** → use `dispatching-parallel-agents` skill with selected profiles

## Routing Examples

**Example 1: "Add a logout button to the settings page"**
- Complexity: SIMPLE (single file, <50 lines, clear path)
- Decision: handle inline, no dispatch

**Example 2: "Investigate why the API returns 500 on large payloads"**
- Complexity: MEDIUM (needs investigation, scoped to API layer)
- Profile: `debugger` (root cause analysis, needs exec)
- Preset: standard
- Dispatch: single `debugger` subagent with error context

**Example 3: "Add OAuth2 authentication with Google and GitHub"**
- Complexity: COMPLEX (multi-system, security, unfamiliar domain)
- Sequence: `researcher` (OAuth2 docs + existing auth patterns) →
  `architect` (design token flow + session management) →
  `implementer` (write code + tests) → `reviewer` (two-axis review)
- Preset: strict (security change)
- Use `subagent-driven-development` if you have a multi-task plan

**Example 4: "Fix 4 failing tests in 3 different test files"**
- Complexity: PARALLEL (independent failures, no shared state)
- Profile: `debugger` per failure
- Preset: standard per failure
- Use `dispatching-parallel-agents` skill

**Example 5: "What version of React does this project use and is it compatible with React 19?"**
- Complexity: MEDIUM (research task, scoped)
- Profile: `researcher` (read-only, cheap, web research)
- Preset: N/A (no implementation to review)
- Dispatch: single `researcher` subagent

## Integration with Existing Skills

This skill is the ENTRY POINT for dispatch decisions. It delegates to:

- `dispatching-parallel-agents` — when routing decision is PARALLEL
- `subagent-driven-development` — when you have a multi-task plan to execute
- `code-review` — when routing decision includes review (reviewer profile)
- `verification-before-completion` — when VFs need to be defined (pre-execution gate)
- `tool-and-skill-discovery` — when no profile fits and you need to find alternatives

Don't bypass this skill when the decision is non-obvious. Don't invoke it
when the decision is obvious — overhead exceeds value.

## Output

Return a one-line routing decision:
```
[complexity] → [profile] (preset: [budget]) → [execution skill]
```

Example: `COMPLEX → researcher → architect → implementer → reviewer (preset: strict) → subagent-driven-development`

## Role Bottleneck Awareness (AgentCARD)

Heterogeneous teams improve accuracy by up to 44% over cost-equivalent homogeneous
teams, and match the strongest homogeneous team at up to 12x lower per-task cost
(arXiv:2606.20629). Bottlenecks are **domain-dependent** and **model-agnostic**:

| Task type | Bottleneck role | Routing implication |
|---|---|---|
| Debugging (SWE-bench-like) | **Planner/architect** (φ_P = +29%) | Use stronger model in architect role |
| Document analysis (FinanceBench-like) | **Executor/reviewer** (φ_E = +34%) | Use stronger model in reviewer role |
| Research (IMO-AnswerBench-like) | **Executor** (φ_E = +34%) | Use stronger model in researcher role |

**How to apply:** When routing, identify which role is critical for the task type.
Assign the strongest available model to the bottleneck role. Assign cheaper models
to non-critical roles. This is orthogonal to complexity-based routing — a simple
task can still have a bottleneck role that needs a strong model.

**Source:** AgentCARD (arXiv:2606.20629). Uses Shapley values to identify role
bottlenecks. Preprint (not peer-reviewed) — findings are directional, not definitive.
