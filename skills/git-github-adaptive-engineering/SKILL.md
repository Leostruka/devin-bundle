---
name: git-github-adaptive-engineering
description: Use when any task touches git history, GitHub issues/PRs/releases/CI, repo governance, or branch and merge decisions. Runs the Fase Zero situational-awareness battery, picks one of five delivery flows via the adaptive decision engine, and enforces commit/PR information-density standards. Orchestrates the gh, git-workflows, github-actions, pr, and debug/finish skills.
triggers: [user, model]
---

# Git/GitHub Adaptive Engineering

Orchestrating skill for all git + GitHub work. Pipeline:

**Fase Zero** (situational awareness) -> **decision engine** (pick the
flow) -> **arsenal** (gh/git commands) -> **density** (commit/PR bodies).

Depth lives in `reference/`: `decision-flows.md` (5 flow patterns),
`gh-arsenal.md` (command/API matrix), `density-templates.md` (copyable
bodies with `Refs:`/`Closes #` wiring and Mermaid).

## Fase Zero: situational-awareness battery

Run before any git/GitHub action that changes state:

```bash
python scripts/phase-zero.py   # read-only JSON diagnostic, offline-safe
```

It probes `git status -sb`, `git branch -a`, `git remote -v`,
`git log -n 5 --oneline`, `gh auth status`, `gh repo view --json ...`
(capabilities + merge strategies), `.github/` tree presence,
`gh api repos/{owner}/{repo}/rulesets` (best-effort), and
`gh workflow list`. Every probe is optional; failures return as
`{ok:false}` entries, never crashes.

Classify the result before acting:

- Tree state: clean/dirty, staged/unstaged, ahead/behind upstream.
- Branch state: detached HEAD, on default branch, existing branch or PR
  already covering the issue.
- Remote/auth: origin reachable, `gh` authenticated, token scopes
  (`gh auth status` shows missing scopes such as `project`).
- Repo capabilities: issues/projects/discussions enabled, allowed merge
  strategies (`mergeCommitAllowed`, `squashMergeAllowed`,
  `rebaseMergeAllowed`), `deleteBranchOnMerge`, repository topics.
- Governance: rulesets, required reviews, environments, CODEOWNERS,
  `.github/` workflows, issue/PR templates present or absent.
- Secrets/variables: `gh secret list`, `gh variable list` (names only,
  never values).

## Adaptive decision engine

Pick exactly one flow from `reference/decision-flows.md`:

| Signal | Flow |
| --- | --- |
| Default: feature, fix, refactor, docs, chore tied to an issue | 1. Feature/fix/refactor delivery |
| Production incident, broken main, security fix | 2. Critical hotfix (fast-track) |
| Cross-module design, new subsystem, breaking API | 3. Architectural change (RFC + ADR) |
| Repo setup, templates, labels, rulesets, CI baseline | 4. Repo governance/bootstrap |
| Red CI, flaky pipeline, workflow misconfiguration | 5. CI self-healing |

Ambiguous signal -> ask one question, then proceed. Never skip Fase
Zero: most git/GitHub failures are wrong state assumptions, not wrong
commands.

## Arsenal (summary; full matrix in `reference/gh-arsenal.md`)

- Issues/PRs: `gh issue|pr create|edit|view|list|close` with
  `--body-file`; `gh pr merge --squash|--merge|--rebase --auto`.
- Hierarchy: `gh issue create --parent`, `gh issue edit --add-sub-issue`,
  `--remove-sub-issue`, `--add-blocked-by`, `--add-blocking` (gh >= 2.94);
  JSON fields `parent`, `subIssues`, `blockedBy`, `blocking`,
  `issueType`.
- Repo metadata: `gh repo view --json ...`, `gh api repos/{o}/{r}/...`
  for rulesets, environments, branches, tags, contents.
- CI: `gh workflow list|view|run`, `gh run list`, `gh run view <id>
  --log-failed`, `gh run watch|rerun|cancel|download`,
  `gh cache list|delete`.
- Releases: annotated tag + `gh release create --generate-notes`;
  `gh attestation verify` for provenance checks.
- Secrets/config: `gh secret set|list|delete`, `gh variable
  set|list|get`; never echo values.
- Projects v2: `gh project list|view|item-add|field-list|item-edit`
  (needs `gh auth refresh -s project`).

## Information-density standards

- Commits: `git commit -F <file>` for anything beyond a trivial
  one-liner; the body carries context, technical detail, decisions and
  trade-offs, validation evidence, and `Refs: #N` wiring.
- PRs: `gh pr create --body-file <file>`; body carries Summary (Mermaid
  when flow matters), Evidence, Merge Danger, validation checklist, and
  `Closes #N` for the issue this PR completes.
- Issues: `--body-file`; problem, scope, acceptance criteria, links.
- Copyable templates: `reference/density-templates.md`.
- Wiring rule: `Closes #N` only where the work actually completes;
  `Refs: #N` everywhere else (commits, follow-ups, docs).

## Delegation map

This skill orchestrates; siblings execute depth:

- `gh` - gh CLI JSON fields, pagination, interactivity policy.
- `git-workflows`, `git-helper` - branches, commits, cleanup.
- `using-git-worktrees` - isolated workspaces.
- `resolving-merge-conflicts` - conflict resolution.
- `github-actions` - workflow YAML security review.
- `debug-ci-failures` - CI diagnosis playbook.
- `pr` - PR body visual standards (Summary/Evidence/Merge Danger).
- `finishing-a-development-branch` - integration and cleanup.
- `deploy` - release/deploy/rollback verification.

## Boundaries

- Never write secrets to files, issues, PRs, or commit messages; use
  `gh secret set` / `gh variable set` and reference by name.
- `phase-zero.py` is read-only; do not extend it to mutate state.
- Destructive git ops (force-push, `reset --hard`, `branch -D`,
  `tag -d`) need explicit per-action user confirmation.
