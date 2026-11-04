# 50 -- No diagram of hook event flow and decision merge

- **Status**: open
- **Category**: diagrams
- **Severity**: P2
- **File**: hooks.v1.json

## Evidence
README.md:79 has one high-level flowchart (user -> rules -> skills ->
tools -> hooks -> verification) but no diagram shows the actual hook
machinery: stdin JSON payload -> aggregator -> inner script chain ->
allow/block JSON on stdout -> exit 0/2. With consolidation, a single
PreToolUse exec call fans out to 7 scripts; the merge precedence and the
fail_closed boundary are exactly the kind of logic a sequence/flow
diagram communicates better than the TOOLS-MAP table (which is itself
stale, see issue 46). `scripts/validate-mermaid.py` + CI
`node --check scripts/mermaid-parse-check.js` already gate mermaid
syntax, so a checked-in diagram is cheap to keep valid.

## Recommendation
Add a mermaid `flowchart` to TOOLS-MAP or a HOOKS-PIPELINE doc:
one lane per lifecycle event, inner-script fan-out for the two
aggregators, block-decision merge node, and the fail_closed/fail-open
annotation.

## Verification
`validate-mermaid.py` accepts the block; diagram entry points equal the
10 commands in hooks.v1.json.
