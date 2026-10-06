# Worktree lanes

Design note for the role isolation model. Mechanics come from
`git-workflows` / `using-git-worktrees`; this note covers only what is
specific to the orchestrator layout.

## Layout

Three layers per role:

| Layer | Path | Writer |
|---|---|---|
| Durable home | `$ROOT/workers/<role>/` (`role.md` + `.devin/` notes/adr) | role, via absolute `$ROOT` paths |
| Code lane | `$ROOT/.worktrees/<role>`, branch `<slug>-<role>` | role, as delegation cwd |
| Shared state | `$ROOT/.devin/` (ledgers, handoffs, vision, adr, research) | orchestrator; role writes only its declared `-out` handoff + report |

`<slug>` is the project slug. `<slug>-<role>` is one lane branch per role,
living as long as the role is active; contracts on the same role share the
lane.

## Why `$ROOT`-absolute paths

A worktree is a separate checkout: tracked files exist in both places, but
untracked or gitignored files (`.devin/handoffs/`, `.devin/ledgers/`,
`workers/<role>/.devin/` when ignored) exist only in the root. Any path the
worker must share with the orchestrator - handoffs, reports, frozen inputs,
VF targets, the durable home - is written in the contract as an absolute
path under `$ROOT`. Relative paths silently fork state across checkouts.

## Lifecycle

1. Activate: role matrix spawns the role; orchestrator creates
   `workers/<role>/` (charter + `.devin/`) and, for writing roles, the lane:
   `git -C "$ROOT" worktree add "$ROOT/.worktrees/<role>" -b <slug>-<role>`,
   ensuring `.worktrees/` is gitignored in the target project.
2. Execute: dispatches run with cwd = `$LANE_PATH`; commits land on
   `$BRANCH`.
3. Land: after the contract verifies, the orchestrator merges `$BRANCH`
   into the integration branch (`finishing-a-development-branch`).
4. Retire: role deactivates -> `git -C "$ROOT" worktree remove
   "$ROOT/.worktrees/<role>"` then `git -C "$ROOT" branch -d
   <slug>-<role>`. The durable home is never removed with the lane.

## Decisions and fallbacks

- `.worktrees/` inside the root keeps every lane under one tree and one
  gitignore entry. Fallback when the target's `.gitignore` is untouchable:
  sibling dir `<repo>-<role>`; record the choice in the ledger.
- Read-only roles (`researcher`, most `reviewer`/`qa-ci` dispatches) get
  `Lane: read-only` and work from the root checkout; no worktree cost.
- Single-writer holds across lanes: the orchestrator is the only writer of
  `.devin/ledgers/` and of contract docs in `.devin/handoffs/`; a worker
  writes only the `-out` handoff and report path its contract declares.
- Merge cadence: the lane branch merges at land time per contract, not per
  commit; conflicts surface at verification, where `qa-ci` still runs.
