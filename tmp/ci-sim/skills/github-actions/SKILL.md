---
name: github-actions
description: Use when writing or reviewing .github/workflows YAML files or debugging CI. GitHub Actions security and best practices - SHA-pinned actions, least-privilege permissions, script injection via PR context, pull_request_target dangers, secrets and OIDC, cache poisoning, matrix and artifacts.
triggers: [user, model]
allowed-tools: [read, exec, grep, edit]
---

# GitHub Actions

CI/CD is the most common place to leak secrets and take supply-chain attacks: the YAML is code that runs with credentials. Editing `.github/workflows/` requires extra review.

## Triggers and scope

- `on: push`/`pull_request`/`workflow_dispatch`/`schedule`/`workflow_call` - the trigger defines who can run it and with what context.
- `pull_request` from a fork runs WITHOUT secrets (safe-ish); `pull_request_target` runs with secrets + write token ON FORK CODE = the most dangerous trigger in Actions. Only with restricted `types:` + checkout of the base (never the head) + minimal permissions, or an `environment:` with manual review.
- `workflow_run`/`workflow_dispatch` with inputs: validate them (`type: choice` when possible).
- `paths:`/`branches:` filters so a README change does not run the whole CI.
- `concurrency:` to cancel redundant runs (`cancel-in-progress: true` on PRs).

## Permissions (the default is dangerous)

- The default `GITHUB_TOKEN` has broad permissions. ALWAYS declare `permissions:` at top level or per job - `contents: read` is the floor; add only what is needed (`pull-requests: write`, `packages: write`).
- Job needing no token: `permissions: {}`.
- `secrets: inherit` in a reusable workflow leaks everything - pass secrets explicitly.

## Script injection (the classic bug)

- NEVER interpolate PR context into `run:`:
  `run: echo "${{ github.event.pull_request.title }}"` - the title is attacker-controlled, `$(rm -rf ~)` executes.
  Correct: env var (`env: TITLE: ${{ ... }}` + `echo "$TITLE"`) or `github-script` with the value as an argument.
- Dangerous contexts: `github.event.issue.title`, `.body`, `pull_request.title`, `.head.ref`, `commits.*.message`, `github.head_ref`. Anything an external user controls does NOT go inline into `run:`.
- Same rule for `env:`/`with:` interpolated directly into `script:` of `actions/github-script`.

## Third-party actions (supply chain)

- Pin by commit SHA, not by tag: `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`. Tags are mutable - the owner can re-point them to malicious code (has happened to popular actions).
- Trust only official orgs (`actions/*`, `github/*`) or audited vendors; an obscure 3-star action running with your token is risk.
- `allowed-actions` at repo/org level restricts what runs.
- Dependabot for actions updates SHAs (`.github/dependabot.yml` with `package-ecosystem: github-actions`).

## Secrets and OIDC

- Secrets via `${{ secrets.X }}` - never `echo` (goes to the log); the runner masks, but formatting breaks masking.
- OIDC (`id-token: write` + aws/azure/gcp role) replaces long-lived cloud keys - preferable to static secrets.
- `environment:` with required reviewers for deploy/prod jobs.
- Secrets into a `run:` step indirectly via env (`env: KEY: ${{ secrets.KEY }}`), never inline in the command (the log shows the command, not the env).
- `ACTIONS_STEP_DEBUG` logs more - do not enable on public repos with secrets.

## Cache and artifacts

- `actions/cache` keyed by lockfile (`hashFiles('**/package-lock.json')`) + `restore-keys` fallback.
- Cache poisoning: can a fork `pull_request` write to the shared cache? No - PR cache is isolated from the base branch (but `pull_request_target` is not). Know the difference.
- Downloading artifacts from another workflow run (`dawidd6/action-download-artifact`) is a surface - untrusted PR artifacts must not go straight into a release.
- Shorter `retention-days` for artifacts holding sensitive data.

## Jobs and matrix

- `strategy.matrix` for multi-version/os; `fail-fast: false` when you want all results.
- `timeout-minutes` on every job (default 6h = runaway runner bill).
- `if:` with explicit `success()`/`failure()`/`always()` - default is "only if previous passed".
- `outputs` between jobs via `needs` - never pass secrets through outputs (goes to metadata log).
- `services:` (postgres/redis) for real integration tests instead of mocks.
- `runs-on: ubuntu-latest` ok; self-hosted runner on a public repo = anyone who opens a PR runs code on your machine - NEVER.

## Reusable workflows and composite actions

- `workflow_call` with declared `inputs`/`secrets`; caller passes explicitly (not `secrets: inherit`).
- Composite action (`action.yml`) for repeated steps; same injection care in `run:`.

## Common review findings

- `pull_request_target` without restriction/protected environment.
- `${{ github.event.* }}` inside `run:` (injection).
- Missing `permissions:` (full-access token).
- Floating-tag action (`@v4`, `@main`) instead of SHA.
- `secrets: inherit` in reusable workflows.
- Secret echoed/printed or passed inline in a command.
- Self-hosted runner on a public repo.
- `continue-on-error` hiding real failure in a required check.
- Checkout of `github.event.pull_request.head.sha` under `pull_request_target` (runs fork code with secrets).
- CI edited without the task requiring it (change in workflow needs justification in the report).

## Cascade

- Secrets in repo/CI: `security` skill.
- Pinned versions of actions/deps: repository pinning rules (versions >7 days published).
- CI files are a protected zone: justify edits in the change report.
