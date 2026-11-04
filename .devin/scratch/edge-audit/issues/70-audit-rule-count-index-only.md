# 70 -- audit rule-count check matches the index, not the rule bodies

- **Status**: resolved
- **Category**: algorithm-translation
- **Severity**: P2
- **File**: audit.py:120-137

## Evidence

Check `[6]` counts lines matching `'\n' + str(i) + '. **'` for i in 1..29.
Those patterns match the "## Rule index" bullets at AGENTS.md:9-32, not the
pinned "## N." section bodies. Merged rules (4, 16, 17, 21, 22) exist only as
index aliases yet still count toward `rule_count` (26). Consequence: deleting
an entire pinned rule body, e.g. Rule 13's authorization section, keeps the
check green as long as the index line survives. The documented contract
("N rules declared") is translated into "N index bullets present".

## Recommendation

Count `^## N.` section headers for the pinned body check, and separately
verify index aliases point at an existing rule number.

## Verification

Delete the body of any pinned rule in AGENTS.md while leaving the index line;
`python audit.py` check 6 still reports OK.

## Answer
Check 6 rewritten: index bullets (`^\d+\. \*\*`) are counted as declared
rules, while `^## N.` / `^### N.` section headers are counted as bodies.
Every non-alias index rule must have a body section (deleting Rule 13's body
now FAILs), and alias bullets (`N. **-> Rule M**`) must point at a declared
rule number. rule_count is compared against the index, matching the
documented contract.
