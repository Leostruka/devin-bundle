---
name: deploy
description: "Use when the user wants to release, deploy, rollback, or verify a deployment pipeline. Covers CI/CD gates, environment checks, canary/blue-green, and post-deploy smoke tests."
triggers: [user, model]
---

# Deploy

Deploy, release, and verify code in target environments.

## When to use

- User asks to deploy, release, or promote to staging/production.
- Rollback is needed.
- Post-deploy smoke tests or health checks are required.
- Need to choose between canary, blue-green, or simple rollout.

## Core protocol

1. **Confirm artifact.** Verify that the build/test/lint gates passed before deploy.
2. **Check environment.** Read deployment config, secrets, and target infrastructure.
3. **Choose strategy.** Canary, blue-green, rolling, or all-at-once based on risk.
4. **Execute deploy.** Use the project's deployment command (e.g., `npm run deploy`, `docker compose up`, `kubectl apply`, `gh workflow run`).
5. **Run smoke tests.** Hit health endpoints, run critical e2e checks.
6. **Verify and report.** Confirm success or trigger rollback.

## See also

- `docker` — container build, run, and compose.
- `deploy` — release orchestration, rollback, and smoke tests.

## Output rule

- After deploy, run smoke tests and report: URL, version, status, rollback command.
- If rollback is needed, run it and verify the previous version is healthy.
