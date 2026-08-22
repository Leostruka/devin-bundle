---
name: grilling
description: Use when exploring and stress-testing ideas before committing to a design or plan, when the user says "grill me" or "stress-test this", or when sharpening a plan while also producing ADRs and a glossary.
---
# Grilling & Brainstorming (Unified)

Two traditions, one pipeline. This skill merges **collaborative brainstorming** (gentle exploration, one question at a time, visual companion, design doc) with **relentless grilling** (design tree, frontier rounds, numbered questions, recommended answers, sub-agents for facts).

## Modes

| Mode | Trigger | What changes |
|---|---|---|
| **Default** | "grill this", "stress-test", "brainstorm" | Full pipeline below |
| **Stateless** | "grill me" without a working directory | Skip file/context exploration (Step 1); work purely from the conversation |
| **With-docs** | "grill and document" / "sharpen plan + ADRs" | Run full pipeline + invoke `domain-modeling` in Phase 3 to produce ADRs and glossary alongside the spec |

## Decision logic: which mode when

| Situation | Use | Why |
|---|---|---|
| Idea is fuzzy, early-stage, need to explore possibilities | **Brainstorm mode** | Gentle, one question at a time. Propose 2-3 approaches with trade-offs. Visual companion for UI/layout questions. |
| Have a plan/decision that needs stress-testing | **Grill mode** | Relentless interview. Design tree with frontier rounds. Every branch visited, nothing silently assumed. |
| New feature from scratch | **Both, in sequence** | Brainstorm to explore the idea → Grill to stress-test the resulting design → Write spec → planning-pipeline (Tickets mode) or writing-plans. |
| Modifying existing behavior | **Brainstorm mode** | Understand current behavior, propose changes, get approval. |
| User says "grill me" or "stress-test this" | **Grill mode** | Explicit trigger for relentless questioning. |
| User says "brainstorm" or "I have an idea" | **Brainstorm mode** | Explicit trigger for collaborative exploration. |
| Design is done, need to write it up | **Brainstorm mode (final phase)** | Write design doc, spec self-review, user review gate, transition to planning-pipeline (Tickets mode) or writing-plans. |

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short, but you MUST present it and get approval.

---

## Phase 1: Explore (Brainstorm Mode)

### 1. Explore project context

Check files, docs, recent commits. Before asking detailed questions, assess scope: if the request describes multiple independent subsystems, flag this immediately. Don't spend questions refining details of a project that needs to be decomposed first.

If the project is too large for a single spec, help the user decompose into sub-projects. Each sub-project gets its own spec → plan → implementation cycle.

### 2. Offer the visual companion just-in-time

NOT upfront. The first time a question would genuinely be clearer shown than described, offer it then (its own message); on approval its browser tab opens. If no visual question ever arises, never offer it. See [visual-companion.md](visual-companion.md) for details.

**This offer MUST be its own message.** Only the offer — no clarifying question, summary, or other content.

### 3. Ask clarifying questions

- One at a time
- Prefer multiple choice when possible, but open-ended is fine
- Focus on understanding: purpose, constraints, success criteria
- For appropriately-scoped projects, refine the idea through dialogue

### 4. Propose 2-3 approaches

- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- YAGNI ruthlessly — remove unnecessary features from every approach

### 5. Present design

- Scale each section to its complexity
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Design for isolation and clarity: break into smaller units with one clear purpose, well-defined interfaces, independently testable

---

## Phase 2: Stress-test (Grill Mode)

### The design tree

Map the design as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled — the questions you can ask now without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

### Question format

```
Q1 - <question title>: <question body, might be multiple paragraphs, including multiple choices>
> <your recommended answer>
```

### Frontier rules

- Each round the user answers reshapes the tree — settled decisions push the frontier outward and unblock questions that depended on them.
- Recompute the frontier and ask the next round.
- A question whose answer depends on another question still open in this round belongs to a later round, not this one.

### Finding facts is your job, never the user's

When a frontier question needs a fact from the environment (filesystem, tools, docs), dispatch a sub-agent to find it — don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait — ask the rest of the frontier now.

The **decisions** are the user's — put each to them and wait.

### When grilling is done

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

---

## Phase 3: Write it up (Brainstorm Mode, final phase)

### Checklist

You MUST complete these in order:

1. **Explore project context** — check files, docs, recent commits
2. **Offer visual companion just-in-time** — only when a visual question arises
3. **Ask clarifying questions** — one at a time (brainstorm mode)
4. **Propose 2-3 approaches** — with trade-offs and recommendation
5. **Present design** — in sections, get user approval after each
6. **Grill the design** — design tree, frontier rounds, stress-test every branch (grill mode)
7. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md` and commit
8. **Spec self-review** — quick inline check (see below)
9. **User reviews written spec** — ask user to review before proceeding
10. **Transition to implementation** — the spec is done. Pick the execution path:
    - **planning-pipeline (Tickets mode)** — split into tracer-bullet vertical-slice tickets with blocking edges, then `implement` per ticket (canonical flow, matches `ask-matt` router)
    - **writing-plans** — turn the spec into a single detailed task-by-task implementation plan, then `executing-plans`

**The terminal state is leaving grilling for one of the two execution paths.** Do NOT start implementing inside grilling — the spec is the deliverable here; execution happens in the next skill.

### Design doc

Write the validated design (spec) to `docs/specs/YYYY-MM-DD-<topic>-design.md` (user preferences for spec location override this default). Commit the design document to git.

### Spec Self-Review

After writing the spec, look at it with fresh eyes:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single implementation plan, or does it need decomposition?
4. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.

Fix any issues inline.

### User Review Gate

After the spec review loop passes, ask the user to review the written spec:

> "Spec written and committed to `<path>`. Please review it and let me know if you want to make any changes before we start writing out the implementation plan."

Wait for the user's response. If they request changes, make them and re-run the spec review loop. Only proceed once the user approves.

---

## Visual Companion

A browser-based companion for showing mockups, diagrams, and visual options. Available as a tool — not a mode.

**Per-question decision:** Even after the user accepts, decide FOR EACH QUESTION whether to use the browser or the terminal. The test: **would the user understand this better by seeing it than reading it?**

- **Use the browser** for content that IS visual — mockups, wireframes, layout comparisons, architecture diagrams
- **Use the terminal** for content that is text — requirements questions, conceptual choices, tradeoff lists, scope decisions

A question about a UI topic is not automatically a visual question. "What does personality mean in this context?" is conceptual — use the terminal. "Which wizard layout works better?" is visual — use the browser.

If they agree to the companion, read [visual-companion.md](visual-companion.md) before proceeding.

---

## Working in existing codebases

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work, include targeted improvements as part of the design — the way a good developer improves code they're working in.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

## Process Flow

```
Explore context
  -> Ask clarifying questions (brainstorm, one at a time)
  -> Propose 2-3 approaches with trade-offs
  -> Present design sections, get approval per section
  -> Grill the design (design tree, frontier rounds)
  -> User confirms shared understanding?
     -> no: revise, re-grill
     -> yes: write design doc
        -> spec self-review (fix inline)
        -> user reviews spec?
           -> changes: revise, re-review
           -> approved: pick execution path
              -> planning-pipeline (Tickets mode) -> implement (canonical)
              -> writing-plans -> executing-plans (detailed single plan)
```
