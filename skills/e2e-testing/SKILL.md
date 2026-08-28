---
name: e2e-testing
description: "Use when the user wants to add, run, or debug end-to-end tests. Covers Playwright, Selenium, Cypress, happy paths, critical user journeys, and CI integration."
triggers: [user, model]
---

# E2E Testing

End-to-end tests for critical user journeys.

## When to use

- New user-facing feature needs regression coverage.
- Critical path broke in production.
- Setting up e2e suite for the first time.
- Debugging flaky e2e tests.

## Core protocol

1. **Map journeys.** Login, checkout, create/read/update/delete, key workflows.
2. **Choose tool.** Playwright, Cypress, Selenium based on project.
3. **Write stable selectors.** Prefer data-testid or role-based selectors.
4. **Mock external dependencies.** Avoid real payments, emails, or third-party APIs.
5. **Run and debug.** Headed for debugging, headless in CI.
6. **Report flakes.** Isolate timing issues and retries.

## Output rule

- One test file per journey.
- Run `npx playwright test` or equivalent and report pass/fail counts.
