---
name: intention-capture
description: Use when capturing and validating the "intent" field in tickets, specs, or PRDs before implementation. Ensures every task has a clear objective, landing zone, and user impact.
triggers: [user, model]
---

# Intention Capture

Captures and validates the "intent" field in tickets, specs, or PRDs. Ensures every task has a clear objective, landing zone, and user impact before implementation begins.

## When to use

- Before creating a ticket or spec in `planning-pipeline`.
- Before implementing a feature or fix.
- When the user's request is ambiguous or lacks context.
- When the PRD or ticket does not have an `Intent` section.

## What to capture

1. **Objective.** What the user wants to achieve.
2. **Landing zone.** Which project, module, or feature the change affects.
3. **User impact.** How the change affects the user or the product.
4. **Boundaries.** What is in scope and what is out of scope.

## Process

```
User requests work
  → Capture intent (objective, landing zone, user impact, boundaries)
  → Validate intent (is it clear? is it complete?)
  → If unclear: ask for clarification
  → If clear: proceed to `planning-pipeline` or `implement`
```

## Example

```markdown
## Intent

- **Objective:** Add OAuth2 login to the mobile app.
- **Landing zone:** `src/auth/` module, `LoginScreen` component.
- **User impact:** Users can sign in with Google or Apple instead of email.
- **Boundaries:** No password reset flow, no social profile sync.
```

## Anti-patterns

- Implementing without knowing the objective.
- Skipping the landing zone and making changes in the wrong module.
- Ignoring user impact and building something nobody wants.
- Vague boundaries that lead to scope creep.

## Cross-skills

- `grilling` — captures intent during the interview process.
- `planning-pipeline` — uses intent to create the PRD and tickets.
- `implement` — enforces intent before writing code.
- `verification-before-completion` — verifies the intent was met.
