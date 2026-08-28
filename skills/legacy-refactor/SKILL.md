---
name: legacy-refactor
description: "Use when the user wants to modernize legacy code incrementally. Covers strangler-fig, seams, characterization tests, safe extraction, and risk reduction."
triggers: [user, model]
---

# Legacy Refactor

Modernize legacy code without big-bang rewrites.

## When to use

- Code is hard to test, read, or change.
- Need to migrate to a new framework or language.
- Want to extract a service from a monolith.
- Technical debt is blocking features.

## Core protocol

1. **Add characterization tests.** Capture current behavior before touching code.
2. **Find seams.** Identify interfaces where new code can replace old code.
3. **Strangle incrementally.** Route small slices through new implementations.
4. **Refactor locally.** Extract functions, rename, reduce duplication.
5. **Verify at each step.** Run tests and, if possible, a diff-check.
6. **Document decisions.** ADRs for architecture changes and deprecated paths.

## Output rule

- Each commit must leave the system testable and no worse than before.
- Before/after: tests, complexity metrics, and migration status.
