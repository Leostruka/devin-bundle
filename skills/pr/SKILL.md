---
name: pr
description: Use when writing a PR body or description — a visual Summary (smallest diagram/diff-sketch/tree that makes the point), concrete Evidence (before/after runs), and Merge Danger (one-way vs two-way door + blast radius). Ported and adapted from mattpocock/skills engineering/pr.
triggers: [user, model]
---

# PR

Use this template for the PR body:

```markdown
## Summary

<diagram, diff-sketch, or tree>

## Evidence

- **Before:** <screenshot/output/failing test run>
  **After:** <screenshot/output/passing test run>

## Merge Danger

**Door:** <one-way or two-way>

**Blast Radius:** <one-word description>
```

Skip preambles; keep prose brief. Use the repo's domain language
(`.devin/CONTEXT.md` glossary when present).

## Summary

Pick the smallest view that makes the key point clear.

- Logic or algorithm -> pseudocode block.
- Runtime control flow -> call tree.
- UI structure -> component tree (include state and module boundaries
  that matter).
- File responsibility or broad refactor -> shallow annotated file tree.
- Interaction/data flow -> Mermaid sequence or flow diagram.
- The point is *what changes* -> `diff` on the shape that already
  exists (component tree, file tree, call tree, or code block). Show
  the whole block instead when most of it is new or the user needs a
  copyable target shape.

Place each visual next to the short text it supports. Keep only the
calls, files, props, states, and boundaries needed for the current
question. Use one or several; do not overwhelm.

## Evidence

Concrete proof the change works, before and after.

- Screenshots are top tier when the change is visual and the
  environment supports capture (use `computer-use` when needed).
- Execution evidence next: the exact test or command that failed
  before and passes now — paste real output, not a summary of it.

## Merge Danger

**Door:** one-way or two-way. Two-way doors roll back cheaply;
destructive or hard-to-reverse changes are one-way and get a sentence
on what makes them irreversible.

**Blast Radius:** one-word scope of possible impact (e.g. layout shift,
consumer breakage, CI contract, migration cost), plus a line when the
ramifications aren't obvious.
