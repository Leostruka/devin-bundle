# Mode: Spec (PRD)

Takes the current conversation context and codebase understanding and
produces a PRD (Product Requirements Document) — a destination document, not a
throwaway. Do NOT interview the user — just synthesize what you already know.

**Spec is a starting point, not a source of truth.** A spec begins to rot on
the first hotfix: a bug is fixed directly in code and the spec becomes a lie.
This is the same law that killed UML/MDA — the model was never the reality,
the code was. Treat the PRD as a destination document that captures intent at
decision time, then let `memory-management` and the emerging code record what
actually got built. Thoughtworks Technology Radar (Nov 2025) places
spec-driven development in the "Assess" ring and warns "we may be relearning a
bitter lesson — that handcrafting detailed rules for AI ultimately doesn't
scale" (<https://www.thoughtworks.com/radar/techniques/spec-driven-development>).
Write the spec, use it to align and to cut tickets, then trust tests and
memory over the document as the work proceeds.

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

## Intent

The final goal, where the feature lands, and how the user is affected. Capture this before any implementation detail. If intent is unclear, stop and use `grilling`.

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

## Estimated size (lines)

Rough estimate of the PR size. If it exceeds ~500 lines, note that it must be split into smaller tickets in Tickets mode.

## Input / Output boundaries

The inputs the feature consumes and the outputs it produces. For APIs, specify request/response shape; for services, specify contracts and data ownership.

## Implementation Decisions

Declare the proposed modules and interfaces affected before any
implementation work. This is the contract surface a reviewer checks against the
spec and the source for tickets or `planning` tasks.

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

