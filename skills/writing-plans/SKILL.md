---
name: writing-plans
description: Use when turning a spec into a concrete, task-by-task implementation plan.
triggers: [user, model]
---
# Writing Plans

## Overview

Write comprehensive implementation plans as destination PRDs - the single source of truth for the feature. Assume the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as vertical-slice, bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

A plan is a living destination document, not a throwaway. Cut tasks as vertical slices (tracer bullets), not horizontal phases (schema → API → UI). Before the first task, declare the proposed modules and interfaces affected. Distinguish disposable prototype assets (scratch files, throwaway scripts) from living assets that ship with the feature.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Input:** A spec (from `grilling` design doc, `planning-pipeline` Spec mode, or any written spec). This is the alternative to `planning-pipeline` (Tickets mode) - use writing-plans when you want a single detailed task-by-task plan for one focused session instead of tracer-bullet tickets for parallel/multi-session work.

**Cross-skills:** Before planning, invoke `deep-mode` if the spec touches unfamiliar code, and `context7` if it depends on a library whose current API you need to verify.

**Cross-skills:** Plans that feed `adaptive-agenda-calendar-routine-engine` map tasks to workbench manifest entries and HH:MM-HH:MM agenda blocks.

**Context:** If working in an isolated worktree, it should have been created via the `/using-git-worktrees` skill at execution time.

**Save plans to:** `.devin/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans - one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- Mark the lifespan of each file:
  - **Living** - code, tests, or docs that remain in the repo after the feature is complete.
  - **Prototype / disposable** - scratch files, one-off scripts, or sample data used to learn or demonstrate a decision, then deleted before merge. Prefix them with `tmp_` or `prototype_`, list them in the step that creates them, and include a step that deletes them.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

Prefer vertical slices (tracer bullets) over horizontal layers. A task that
delivers a complete, end-to-end behavior - however narrow - gives feedback
earlier and keeps the plan demoable. Avoid tasks that are purely "schema",
"API", or "UI" unless they are a pure refactor with no vertical path. Wide
refactors are the exception; sequence them as expand–contract, not as a slice.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use /dispatching-parallel-agents (recommended) or /executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. Record the gate evidence per step. If anything in "STOP
> conditions" occurs (including a drift-check mismatch), stop and report;
> do not improvise. When done, emit the executor report format below.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Planned at:** <sha8> (<YYYY-MM-DD>), output of `git rev-parse --short=8 HEAD` at write time

## Global Constraints

[The spec's project-wide requirements - version floors, dependency limits,
naming and copy rules, platform requirements - one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

## Proposed Modules and Interfaces (optional for small plans)

[Modules, files, and interfaces the work touches - function names,
signatures, data contracts, API endpoints. This is the contract surface a
reviewer checks before any task. Small plans may reference the spec or keep
this to one line.]

---
```

## Task Structure

Title the task by the end-to-end behavior it makes work, not by the layer it touches. A task called "Build the import API" is horizontal; a task called "User can preview an import before confirming" is a vertical slice.

````markdown
### Task N: [End-to-end vertical slice]

**Files:**
- Create (living): `exact/path/to/file.py`
- Create (prototype / disposable): `tmp_prototype.py` (delete in Step X)
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks - exact signatures]
- Produces: [what later tasks rely on - exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]

**Assets:**
- Living: files that ship with the feature.
- Prototype / disposable: `tmp_*` or `prototype_*` files used to learn or
  demonstrate a decision and deleted before merge. Omit this section if
  every file is living.

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Executor-proof plan contract

Every generated plan is executed by a model with zero context, often a
cheaper executor in an isolated worktree. The plan must be mechanically
verifiable end to end; a plan missing any element below fails its own gate.

**Drift check (executor runs FIRST).** The plan stamps `Planned at: <sha8>`.
Before touching code the executor runs `git rev-parse --short=8 HEAD` (the
stamp command; plain `--short HEAD` may abbreviate to 7 chars and is NOT the
check); if it differs from the stamp, STOP and report (the plan may be
stale). Then run `git diff --stat <sha8>..HEAD -- <in-scope paths>`; any
change to an in-scope file means compare the plan's "current state"
excerpts against the live code, and a mismatch is a STOP condition.

**Verify per step.** Every step already ends with `Run:` + `Expected:`;
treat it as a hard gate: run the command, compare output to expected, and
record the excerpt as evidence in the executor report. A step without a
runnable gate is a plan defect; fix the plan before handing it off.

**STOP conditions.** Every plan MUST enumerate its own STOP conditions
(plan-specific risks, not boilerplate). The defaults that must appear when
relevant:

- Drift: HEAD SHA or in-scope diff diverged from `Planned at`.
- A step is unverifiable: its gate command cannot run, or the expected
  output cannot be checked against reality.
- A verification gate fails twice after a reasonable fix attempt.
- The fix appears to require editing an out-of-scope file.
- A "current state" excerpt no longer matches the live code.

**Executor report format.** The executor's final message MUST use this
shape:

```text
STATUS: DONE | BLOCKED | PARTIAL
PLANNED-AT: <sha8>  HEAD: <sha8>  DRIFT: none | <summary>
STEPS:
  - Step N <title>: PASS | FAIL | SKIPPED - files: <paths> - gate: `<cmd>` -> <output excerpt>
FILES CHANGED: <list, or "none">
NOTES: <deviations, rejected-approach hits, follow-ups>
```

**Rejected approaches registry.** Every plan MUST name where rejected
alternatives are recorded so they are not re-proposed: append a
`## Rejected approaches` section to the plan (one line per rejected option
plus rationale), or, when the plan belongs to a batch, reference the batch
index's "Findings considered and rejected" section (e.g.
`.devin/plans/README.md`). An executor that discovers a better approach
mid-flight records it there instead of silently switching.

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** - never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code - the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task
- Prototype / disposable files with no step that deletes them before merge

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself - not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags - any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**4. Vertical-slice scan:** Are the tasks ordered by end-to-end user-facing behavior, not by technical layer? If a task is "write the schema" or "add the API" with no user-facing test, it is probably a horizontal slice.

**5. Asset-lifespan scan:** Every `tmp_*` or `prototype_*` file has a matching deletion step; no disposable asset survives in the final commit.

If you find issues, fix them inline. No need to re-review - just fix and move on. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `.devin/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use /dispatching-parallel-agents
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use /executing-plans
- Batch execution with checkpoints for review
