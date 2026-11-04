# 51 -- Composite pipelines (thermos dual-lane, de-slop sequence) lack diagrams

- **Status**: open
- **Category**: diagrams
- **Severity**: P3
- **File**: skills/thermos/SKILL.md

## Evidence
`thermos` orchestrates dual-lane parallel review and `de-slop` sequences
`lean-code`/`no-comments`/`unslop`/thermo per diff (CHANGELOG
[Unreleased], #295). Neither SKILL.md contains a mermaid or ASCII
diagram; ordering and lane-merge semantics are described only in prose.
These are the two bundle skills where execution order is the contract, so
prose-only specs are the easiest to drift. The
export/install round-trip cycle (live config -> mask -> stage -> audit ->
commit) likewise has no dedicated diagram beyond the small README
flowchart snippet at line 239.

## Recommendation
Add one mermaid sequence/flow diagram per composite skill (thermos lane
split + merge, de-slop step order with skip conditions), plus one for the
export cycle in TOOLS-MAP or a new EXPORT-CYCLE doc.

## Verification
Diagrams render via `scripts/validate-mermaid.py`; step labels match the
SKILL.md step names verbatim.
