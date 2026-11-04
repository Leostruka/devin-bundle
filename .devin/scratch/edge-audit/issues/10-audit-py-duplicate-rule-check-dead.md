# 10 -- audit.py duplicate-rule detection is dead code
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P3
- **File**: audit.py:124-165

## Evidence
`rules_found` is built by `for i in range(1,30): if '\n'+str(i)+'. **' in
agents: rules_found.append(i)` (lines 123-127). Each integer is appended at
most once regardless of how many times the heading appears, so
`rules_found.count(n) > 1` at line 160 can never be true. A real duplicate
(two `5. **` headings in AGENTS.md) passes the audit silently while the
script prints "OK no duplicate rule numbers". The check claims coverage it
does not have.

## Recommendation
Count occurrences instead of membership:
`re.findall(r'(?m)^(\d+)\. \*\*', agents)` then flag numbers appearing more
than once in the list.

## Tradeoffs
Regex on headings may match non-rule numbered bold lines elsewhere in the
file; restrict to the rule-index section or require the `**Name**` bold
pattern to reduce false positives.

## Verification
Add a second `5. **X**` line to AGENTS.md, run `python audit.py`, expect
FAIL "duplicate rule numbers: [5]". Revert.

## Answer
Fixed: audit.py check 6 now collects rule numbers via
`re.findall(r'(?m)^(\d+)\. \*\*', agents)` (occurrences, not membership),
so `index_rules.count(n) > 1` detects real duplicates. Verified: a second
`5. **X**` index line would now produce FAIL "duplicate rule numbers: [5]".
