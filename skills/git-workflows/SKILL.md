---
name: git-workflows
description: Use when managing branches, writing commits, creating isolated worktrees for feature work, or resolving and verifying merge/rebase conflicts.
triggers: [user, model]
---

# Git Workflows

Branches, commits, isolated worktrees, and merge-conflict resolution.

## Branches & commits

- `git checkout -b feature/<name>` / `git push -u origin feature/<name>`.
- Conventional commits: `type(scope): description` — feat, fix, docs, style,
  refactor, test, chore. Subject ≤72 chars; atomic commits (one logical change).
- Pull latest before branching; prefixes: feature/, bugfix/, hotfix/.
- Cleanup: `git remote prune origin`, `git branch -d <name>`.

## Worktrees (isolated workspaces)

Core principle: detect existing isolation → prefer native tools → git
fallback. Never fight the harness.

**Step 0 — detect existing isolation:**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
git rev-parse --show-superproject-working-tree 2>/dev/null  # submodule guard
```

`GIT_DIR != GIT_COMMON` and not a submodule → already in a linked worktree;
skip creation. In a submodule → treat as normal repo.

**Step 1a — native worktree tool preferred** (`EnterWorktree`, `/worktree`,
`--worktree` flag): use it — it owns placement, branching, cleanup. Manual
`git worktree add` alongside a native tool creates phantom state.

**Step 1b — git fallback** (no native tool): pick directory in priority
order — explicit user instruction → existing `.worktrees/` → `worktrees/` →
default `.worktrees/`. MUST `git check-ignore -q <dir>` first; if not
ignored, add to `.gitignore` and commit. Then:

```bash
git worktree add "$path" -b "$BRANCH_NAME" && cd "$path"
```

Permission error → sandbox fallback: work in place.

**Step 2 — setup:** auto-detect (package.json→npm install, Cargo.toml→cargo
build, requirements.txt/pyproject.toml→pip/poetry, go.mod→go mod download).

**Step 3 — baseline:** run project tests; failures → report + ask, passes →
"Worktree ready at <path>, <N> tests passing".

Rationalizations to reject: "obviously not in a worktree" (run Step 0),
"worktree add is quicker" (native tool owns lifecycle), "surely ignored"
(run check-ignore), "baseline can wait" (dirty baseline makes later failures
ambiguous).

## Merge conflicts

1. **See the state** — merge/rebase status, history, conflicting files.
2. **Find primary sources** — why each change was made: commit messages, PRs,
   original issues (`gh` for GitHub).
3. **Resolve each hunk** — preserve both intents where possible; where
   incompatible, pick the one matching the merge's stated goal and note the
   trade-off. Don't invent new behavior. Always resolve; never `--abort`.
4. **Run the project's checks** — typecheck, tests, format. Fix what the
   merge broke.
5. **Finish** — stage, commit; `git rebase --continue` until done if rebasing.

## Cross-skills

- `finishing-a-development-branch` — when the branch/worktree is done.
- `handoff` — pause and resume in a fresh session.
- `gh` — read PRs/issues behind conflicting changes.
