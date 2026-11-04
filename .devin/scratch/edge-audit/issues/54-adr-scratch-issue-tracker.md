# 54 -- No ADR for .devin/scratch file-based issue tracker over GitHub Issues

- **Status**: resolved
- **Category**: adr
- **Severity**: P3
- **File**: .devin/agents/issue-tracker.md

## Evidence
`.devin/agents/issue-tracker.md` prescribes Markdown issues under
`.devin/scratch/<effort>/issues/NN-slug.md` plus spec.md/map.md, and
`.devin/issues/` holds a second flat set (`ISSUE_01_*.md`,
`MILESTONE_2_*`). Meanwhile CHANGELOG entries cite GitHub PR numbers
(#289-#296), so two tracking systems coexist with no recorded decision
about scope division (what belongs in scratch vs .devin/issues vs a PR).
The choice of in-repo files (offline, diffable, agent-consumable) over
GitHub Issues is defensible but unwritten; contributors cannot tell
which tracker is authoritative or why.

## Recommendation
Add an ADR: context (agent-driven workflows need issues the agent can
read/write), decision (.devin/scratch per-effort for work items;
`.devin/issues/` backlog semantics defined or deprecated), consequences
(no cross-linking to PRs, numbering local to effort).

## Tradeoffs
In-repo issues do not notify, have no assignee state, and duplicate
across clones; the ADR should accept these costs explicitly.

## Verification
ADR exists; `.devin/agents/issue-tracker.md` links to it; the two issue
dirs' roles are stated in one sentence each.

## Answer

Wrote `.devin/adr/007-scratch-issue-tracker.md` (Accepted): agent-driven in-repo tracking, scope split scratch=per-effort work items vs .devin/issues/=milestone/design, accepted costs. `.devin/agents/issue-tracker.md` now links the ADR and states both dirs' roles.
