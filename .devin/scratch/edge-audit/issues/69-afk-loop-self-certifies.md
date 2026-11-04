# 69 -- afk-loop resolution status is self-certified by the agent

- **Status**: open
- **Category**: investigative-cycles
- **Severity**: P3
- **File**: skills/afk-loop/SKILL.md (per-issue loop, Verification section)

## Evidence

The loop instructs the agent to "Set `Status: resolved`" on the issue file
itself and to mark work done after running TDD in a worktree. Nothing outside
the agent's own narration enforces that:

- No script validates that an issue marked `resolved` has a linked commit,
  passing tests, or a ledger entry.
- The `Blocked by` DAG is parsed from free-text lines the agent also writes;
  a ticket can be resolved without its blockers being real.
- Final verification ("run the project audit, run held-out tests, update the
  ledger") is a checklist in prose; skip it and the loop still terminates
  cleanly with "no ready issues remain".

The ledger and issue files are evidence-shaped but agent-authored end to end,
so the cycle can terminate with plausible artifacts and zero verification.

## Recommendation

Add a small validator (`scripts/check-issue-resolution.py` or an audit.py
check) that fails when an issue file says `resolved` but lacks an `## Answer`
section plus a commit SHA or test reference. afk-loop's stop condition can
then call it.

## Verification

Manually set `Status: resolved` on any open issue with no Answer section;
nothing in `python audit.py` or the hooks flags it.
