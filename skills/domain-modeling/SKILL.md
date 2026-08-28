---
name: domain-modeling
description: Use when building or refining a project's domain model, glossary, or bounded contexts.
agent: architect
---
# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline — challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `.devin/CONTEXT.md` for vocabulary is not this skill — that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## Cross-skills

- If the domain involves an industry-specific term or a concept you're unsure about, invoke `research` to find authoritative definitions before adding it to `.devin/CONTEXT.md`.
- If the domain model is being built inside a large or unfamiliar codebase, invoke `deep-mode` to map how the code currently uses the terms.
- If the term is AI-coding jargon (context engineering, harness engineering, etc.), invoke `ai-coding-dictionary` to keep the project glossary aligned with the bundle's canonical vocabulary.

## File structure

Most repos have a single context:

```
/
├── .devin/
│   ├── CONTEXT.md
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `.devin/CONTEXT-MAP.md` exists, the repo has multiple contexts. The map points to where each one lives:

```
/
├── .devin/
│   ├── CONTEXT-MAP.md
│   ├── adr/                          ← system-wide decisions
│   └── contexts/
│       ├── ordering/
│       │   ├── CONTEXT.md
│       │   └── adr/                  ← context-specific decisions
│       └── billing/
│           ├── CONTEXT.md
│           └── adr/
└── src/
```

Create files lazily — only when you have something to write. If no `.devin/CONTEXT.md` exists, create one when the first term is resolved. If no `.devin/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `.devin/CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update .devin/CONTEXT.md inline

When a term is resolved, update `.devin/CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`.devin/CONTEXT.md` should be totally devoid of implementation details. Do not treat `.devin/CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
