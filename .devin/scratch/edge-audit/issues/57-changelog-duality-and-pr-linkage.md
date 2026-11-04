# 57 -- CHANGELOG vs EXECUTION_CHANGELOG duality; PR refs unresolvable locally

- **Status**: resolved
- **Category**: traceability
- **Severity**: P3
- **File**: .devin/EXECUTION_CHANGELOG.md

## Evidence
Two changelogs coexist with no stated relationship: root `CHANGELOG.md`
(Keep-a-Changelog, release-driven, PR refs like `#293`) and
`.devin/EXECUTION_CHANGELOG.md` (114 lines, pt-BR, scoped to the single
`refactor/bundle-globalization` effort, last describing swe-1-7 routing
that ADR-002 marks superseded). It is unclear whether
EXECUTION_CHANGELOG is a frozen historical artifact or a living file;
nothing links it from README/CONTEXT. Separately, every CHANGELOG entry
cites `(#NNN)` GitHub PRs, but the repo's own tracker is `.devin/scratch`
(issue 54), so local traceability stops at a PR number; research/plans/
handoffs under `.devin/` are not indexed by change, so reconstructing
WHY a subsystem exists (e.g. laya-guard, thermos) requires archaeology
across `.devin/research/` filenames.

## Recommendation
State each file's contract in CONTEXT.md (EXECUTION_CHANGELOG = frozen
per-effort logs under `.devin/`, CHANGELOG.md = release notes), move or
annotate the stale file, and add an index (e.g. `.devin/research/INDEX.md`
or `related:` fields in ledger frontmatter) mapping subsystems to their
research/plan/handoff artifacts.

## Verification
For three recent subsystems (thermos, laya-guard, shorts-factory), a
reader can reach the originating research/plan doc in <=2 hops from
CHANGELOG or manifest.

## Answer

CONTEXT.md gained a `## Changelog contracts` section: CHANGELOG.md = release notes with GitHub PR refs, EXECUTION_CHANGELOG.md = frozen per-effort artifact (do not append), new per-effort logs under .devin/scratch/. Created `.devin/research/INDEX.md` mapping subsystems (thermos, laya-guard, memory, computer-use, etc.) to research/plan/ADR artifacts.
