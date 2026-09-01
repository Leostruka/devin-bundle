---
name: planning-pipeline
description: Use when turning conversation into a written spec, breaking a plan or spec into independent traceable tickets, or when a decision cannot be fully answered and needs input from another person via a questionnaire.
triggers: [user, model]
---
# Planning Pipeline

Three tools for the planning phase, used at different points in the flow from
idea to implementation. Pick the mode that matches the need.

| Mode | Trigger | What it produces |
|---|---|---|
| **Spec** | "Write a spec", "turn this into a spec" | A written spec from conversation context |
| **Tickets** | "Break this into tickets", "split into tasks" | Vertical-slice tickets with blocking edges |
| **Questionnaire** | "I need to ask someone", "can't answer this alone" | A questionnaire document for external input |

The issue tracker and triage label vocabulary should have been provided to
you — run `tool-and-skill-discovery` if not.

**Cross-skills:** invoke `deep-mode` before Spec mode if the codebase is unfamiliar or large, and `context7` when the spec depends on a specific library's current API. Invoke `review-cadence` first if you don't know whether the request needs full planning or can move straight to implementation.

---

## Mode: Spec

Takes the current conversation context and codebase understanding and
produces a PRD (Product Requirements Document) — a destination document, not a
throwaway. Do NOT interview the user — just synthesize what you already know.

### Process

1. Explore the repo to understand the current state of the codebase, if you
   haven't already. Use the project's domain glossary vocabulary throughout
   the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing
   seams should be preferred to new ones. Use the highest seam possible. If
   new seams are needed, propose them at the highest point you can. The fewer
   seams across the codebase, the better — the ideal number is one.

   Check with the user that these seams match their expectations.

3. Write the spec using the template below, then publish it to the project
   issue tracker. Apply the `ready-for-agent` triage label — no need for
   additional triage.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

Declare the proposed modules and interfaces affected before any
implementation work. This is the contract surface a reviewer checks against the
spec and the source for tickets or `writing-plans` tasks.

A list of implementation decisions that was made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified — function names,
  signatures, data contracts, and API endpoints
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions
- Which assets are **living** (ship with the feature) and which are
  **prototype/disposable** (temporary scripts or sample data that must be
deleted before the feature is considered done)

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>

---

## Mode: Tickets

Break a plan, spec, or conversation into a set of **tickets** — tracer-bullet
vertical slices, each declaring the tickets that **block** it.

### Process

#### 1. Gather context

Work from whatever is already in the conversation context. If the user passes
a reference (a spec path, an issue number or URL) as an argument, fetch it
and read its full body and comments.

#### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the
current state of the code. Ticket titles and descriptions should use the
project's domain glossary vocabulary, and respect ADRs in the area you're
touching.

Look for opportunities to prefactor the code to make the implementation
easier. "Make the change easy, then make the easy change."

#### 3. Declare proposed modules and interfaces

Before cutting tickets, list the modules and interfaces the work touches.
This surfaces contract changes and prevents horizontal decomposition. Keep it
short: module/area names, the functions or endpoints affected, and the data
contracts that change. For tiny features, a single line is enough.

#### 4. Draft vertical slices

Break the work into **tracer bullet** tickets — vertical, end-to-end slices,
not horizontal phases.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests) — vertical, NOT a horizontal slice of one layer or phase
- Title and order slices by user-facing end-to-end behavior, not by layer. Example: "User can save a draft" not "Design the schema"
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

Give each ticket its **blocking edges** — the other tickets that must
complete before it can start. A ticket with no blockers can start immediately.

**Wide refactors are the exception to vertical slicing.** A **wide refactor**
is one mechanical change — rename a column, retype a shared symbol — whose
**blast radius** fans across the whole codebase, so a single edit breaks
thousands of call sites at once and no vertical slice can land green. Don't
force it into a tracer bullet; sequence it as **expand–contract**. First
expand: add the new form beside the old so nothing breaks. Then migrate the
call sites over in batches sized by blast radius (per package, per
directory), each batch its own ticket blocked by the expand, keeping CI green
batch to batch because the old form still exists. Finally contract: delete
the old form once no caller remains, in a ticket blocked by every migrate
batch. When even the batches can't stay green alone, keep the sequence but
let them share an integration branch that all block a final
integrate-and-verify ticket — green is promised only there.

#### 5. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work

Ask the user:

- Does each ticket feel like a tracer bullet — a complete, end-to-end vertical slice — rather than a horizontal phase like "schema" or "API"?
- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct — does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?
- Are any proposed assets prototype/disposable (e.g., `tmp_*` scripts)? If so, which ticket deletes them?

Iterate until the user approves the breakdown.

#### 6. Publish the tickets to the configured tracker

Publish the approved tickets. **How** depends on the tracker
`tool-and-skill-discovery` configured — the tickets are the same either way,
only the shape of the blocking edges changes:

- **Local files** → write one file per ticket under
  `.devin/scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in
  dependency order (blockers first). Each file's "Blocked by" lists the
  numbers/titles it depends on. Use the per-ticket file template below — one
  ticket per file, never a single combined file.
- **A real issue tracker (GitHub, Linear, …)** → publish one issue per ticket
  in dependency order (blockers first) so each ticket's blocking edges can
  reference real identifiers. Use the platform's native blocking / sub-issue
  relationship where it has one; otherwise set each ticket's "Blocked by" to
  the blocking issues. Apply the `ready-for-agent` triage label unless
  instructed otherwise — the tickets are agent-grabbable by construction.

Work the **frontier**: any ticket whose blockers are all done. For a purely
linear chain that means top to bottom.

Do NOT close or modify any parent issue.

<local-ticket-template>

# <NN> — <Ticket title>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective — not a layer-by-layer implementation list.

**Proposed modules / interfaces affected:** module/area names and the contracts this slice touches. Omit for tiny slices.

**Blocked by:** the numbers/titles of the tickets that gate this one, or "None — can start immediately".

**Status:** ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective — not layer-by-layer implementation.

## Proposed modules / interfaces affected

Module/area names and the contracts this slice touches. Omit for tiny slices.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- A reference to each blocking ticket, or "None — can start immediately".

</issue-template>

In either form, avoid specific file paths or code snippets — they go stale
fast. Exception: if a prototype produced a snippet that encodes a decision
more precisely than prose can (state machine, reducer, schema, type shape),
inline it and note briefly that it came from a prototype. Trim to the
decision-rich parts — not a working demo, just the important bits.

---

## Mode: Questionnaire

Turn something the user can't answer alone into a **questionnaire** — a
Markdown document they hand to one person to fill in async, or fill out
together over a meeting. The recipient holds knowledge the user lacks; the
questionnaire pulls it out of them.

**Grill the send, not the subject.** Interview the user only about the
_send_, which they can always answer: who it goes to, and what they need
back. The questions in the document then target the **gap** between what the
recipient knows and what the user needs.

1. **Who is it going to?** Ask, in one exchange, the recipient's role,
   expertise, and relationship to the user. This fixes the questionnaire's
   tone and how much context it must carry. Done when you know who the
   recipient is and what they know that the user doesn't.

2. **What do you need back?** Ask, in one exchange, the specific decisions or
   facts the user can't resolve alone and needs from this person. Done when
   you have a concrete list of what the user must walk away able to do or
   decide.

3. **Write the questionnaire.** Draft questions aimed at the gap from steps
   1–2, following the Document structure below. Write it to
   `questionnaire-<slug>.md` in the current directory (slug from the
   topic) and report the path. Done when the file exists and every item the
   user named in step 2 is covered by a question.

### Document structure

Frame the document as a **discovery questionnaire**: the user lacks context,
the recipient holds it. Order questions most-important-first — async means
you may only get one pass — and group them under `##` headings by theme once
there are more than a handful. Write it using the template below.

<questionnaire-template>

# <Questionnaire title>

**Purpose:** why this questionnaire exists and the decision riding on it.

**From:** <the user> — **To:** <the recipient> — **How your answers will be used:** <where they go>

## Context

One paragraph orienting a recipient who wasn't in the user's head. Enough to answer well, not a page.

## How to answer

Deadline and rough effort. Partial answers and "I don't know" are useful — flag anything you're unsure of rather than skipping it.

## <Theme heading>

One `##` section per theme. Under each, its questions, most-important-first. Every question is one idea — never compound — with an answer stub directly beneath, and a one-line _why this matters_ only where the question could be misread or invite a throwaway answer.

<question-example>
### What load is the system expected to handle at launch?

_Why this matters: it decides whether we provision for burst traffic now or defer it._

>
</question-example>

## Anything else?

A closing catch-all: anything we didn't ask that we should know?

</questionnaire-template>
