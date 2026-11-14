# ADR 009: Adaptive Git/GitHub engineering engine

## Status

Accepted

## Context

Git and GitHub work in this repo spans branches, commits, issues, PRs,
releases, CI, rulesets, secrets, and labels. Existing skills (`gh`,
`git-workflows`, `github-actions`, `pr`, `debug-ci-failures`,
`finishing-a-development-branch`, `resolving-merge-conflicts`,
`using-git-worktrees`, `git-helper`) each cover one slice, but no skill
decides which slice applies or enforces traceability between them.
Issue #612 asked for a Microsoft/GitHub-flavored standard: issue-first
traceability, information-dense commit/PR bodies, and a
situational-awareness pass before state changes.

Fixed one-size-fits-all scripts were rejected: the right flow depends on
repo state (clean/dirty tree, auth scopes, rulesets, existing PRs) that
only a read-only probe can establish.

## Decision

Ship `skills/git-github-adaptive-engineering` as an orchestrating
skill, not a fixed pipeline:

1. **Fase Zero**: `scripts/phase-zero.py` runs a read-only diagnostic
   (git state, remotes, `gh` auth, repo capabilities, `.github/` tree,
   rulesets, workflows) and emits an envelope-v2 JSON report; every
   probe is optional and failures degrade to `{ok:false}` entries.
2. **Adaptive decision engine**: five flows (feature/fix/refactor,
   hotfix, architectural change, repo governance/bootstrap, CI
   self-healing) selected from Fase Zero signals.
3. **Orchestrator + executors**: the engine orchestrates; sibling skills
   execute their existing depth. Siblings gained only a pointer to the
   engine; no body rewrites.
4. **Density standards**: commit/PR/issue templates with `Refs: #N` /
   `Closes #N` wiring live in `reference/density-templates.md`.
5. **ADR location**: `.devin/adr/` per this repo's convention. The issue
   text mentioned `docs/adr/`; the decision is recorded here instead.

## Consequences

- Every git/GitHub task starts with a cheap read-only probe; wrong-state
  assumptions (the dominant failure class) are caught before mutation.
- Commit and PR bodies become denser by convention; `Closes #N` wiring
  is enforced by `.github/PULL_REQUEST_TEMPLATE.md` and the pr-quality
  workflow.
- The engine adds one SKILL.md hop before sibling skills; acceptable
  because it replaces ad-hoc per-task flow decisions.
- `phase-zero.py` must stay read-only; mutating probes belong to the
  executor skills.
- Issue forms, release-note categories, dependabot, and pr-quality CI
  in `.github/` encode the same label taxonomy the skill documents.
