# Delegation contract

Filled per dispatch, saved to `.devin/handoffs/<NN>-<role>-<slug>.md` before
the `run_subagent` call. The dispatch prompt carries: one line of project
context, this contract's path, the input artifact paths, and the report
path. Nothing else.

## Contract

- **Contract ID**: <NN>-<role>-<slug>
- **Objective**: <one domain, self-contained>
- **Profile**: <researcher|architect|implementer|reviewer|qa-ci|debugger|domain|subagent_general>
- **Lane**: <branch/worktree path or "read-only">
- **Inputs**: <artifact paths the worker reads first>
- **Output**: handoff-doc at `.devin/handoffs/<NN>-<role>-<slug>-out.md` + report file
- **Tools allowed**: <tool list or "profile default">
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
