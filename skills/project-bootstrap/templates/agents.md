# Project agent rules

This file is included in the agent's context for this project. Keep it concise; only rules that change the agent's behavior belong here. Generic rules live in the global bundle.

## 1. Intent and boundaries before code

- If uncertain, ask — don't guess.
- Declare the intent, user-visible impact, and boundaries (inputs/outputs, scope, non-goals) before writing code.
- Use the smallest solution that solves the problem. Reject overengineering.

## 2. Code style

- <!-- Stack-specific rules go here. Examples:
  - TypeScript: never use `any`; prefer strict types.
  - Python: follow PEP 8; use type hints where it clarifies intent.
  - Run linters after finishing a task. -->

## 3. Testing

- Tests verify intent, not just behavior.
- Don't delete, disable, or skip tests without explicit approval.
- Run the test suite before declaring a task done.

## 4. Security

- Never output or log secrets, tokens, passwords, or API keys.
- Never commit secrets to the repository.
- Treat user input as untrusted; validate and sanitize before use.
- Default endpoints, storage URLs, and services to private. Public endpoints require documented justification.
- Use secure defaults: confirmations for destructive actions, hidden credentials, least privilege.

## 5. Task size

- Keep PRs around 300 lines of change.
- If a task will exceed 500 lines, break it into smaller tasks with clear boundaries.
- Every ticket/spec must include the intent and the "why".
