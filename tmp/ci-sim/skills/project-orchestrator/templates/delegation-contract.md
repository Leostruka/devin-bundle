# Delegation contract

Filled per dispatch, saved to `.devin/handoffs/<NN>-<role>-<slug>.md` before
the `run_subagent` call. The dispatch prompt carries: one line of project
context, this contract's path, the input artifact paths, and the report
path. Nothing else.

## Contract

- **Contract ID**: <NN>-<role>-<slug>
- **Objective**: <one domain, self-contained>
- **Profile**: <researcher|architect|implementer|reviewer|qa-ci|debugger|domain|subagent_general>
- **Lane**: worktree per writing role (default) or "read-only"
  - **Path**: `$LANE_PATH` = `$ROOT/.worktrees/<role>`; `$BRANCH` = `<slug>-<role>`; `$ROOT` = project root (fallback: sibling dir `<repo>-<role>` when `.gitignore` is untouchable)
  - **Lane setup**: `git -C "$ROOT" worktree add "$LANE_PATH" -b "$BRANCH"` plus ensuring `.worktrees/` is gitignored in the target; run by the orchestrator at lane creation
  - **Lane teardown**: merge `$BRANCH` into the integration branch, then `git -C "$ROOT" worktree remove "$LANE_PATH"` and `git -C "$ROOT" branch -d "$BRANCH"`; run when the lane lands
  - **`$ROOT` rule**: handoffs, reports, frozen inputs and VFs resolve as absolute paths under `$ROOT`, never against the worktree cwd - untracked `.devin/` files are not shared between checkouts
- **Inputs**: <artifact paths the worker reads first>
- **Readable refs**: <root docs the worker may read (e.g. `.devin/adr/003-*.md`, `.devin/vision.md`), or "none"> - the only root context a worker sees besides its inputs
- **Frozen inputs**: <path> sha256:<hash> per spec file the worker must not change; orchestrator records at dispatch and re-hashes at verify; drift fails the contract (`certutil -hashfile` on Windows, `shasum` on POSIX)
- **Output**: handoff-doc at `$ROOT/.devin/handoffs/<NN>-<role>-<slug>-out.md` + report file (absolute `$ROOT` paths)
- **Tools allowed**: <tool list or "profile default">
- **Peer consults**: [<role>] max <N>, or "none" - worker emits `CONSULT:` in the handoff; the orchestrator relays, never a direct channel
- **Boundaries (do NOT)**:
  - files/areas not to touch
  - actions not to take
- **Termination**: max <N> turns / max <N> minutes / stop conditions: <list>
- **Verification (VFs)**: commands that prove the output
  - VF1: `<command>` -> expect <result>

## Result (orchestrator fills after return)

- status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
- VFs re-run independently: pass/fail per VF
- ledger line appended: yes
