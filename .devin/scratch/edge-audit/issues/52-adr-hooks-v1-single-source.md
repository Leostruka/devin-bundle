# 52 -- No ADR for hooks.v1.json as single source over config.json.hooks

- **Status**: open
- **Category**: adr
- **Severity**: P2
- **File**: .devin/docs/TOOLS-MAP.md:134

## Evidence
TOOLS-MAP states `hooks.v1.json` is the "Fonte única de hooks" rendered
into `config.json.hooks` at install. This inverts the naive layout
(editing live `config.json` directly) and has real consequences: live
hook edits are lost on next install, `render-user-hooks.py` exists to do
the merge, and drift between the two surfaces is a known failure class
(the 3.18.0 Windows split-brain incident). The decision is recorded only
as one table cell, not as an ADR with context (why not edit
config.json.hooks, why a versioned template name "v1").

## Recommendation
Add `.devin/adr/005-hooks-single-source.md`: context (live-vs-repo
split, install rendering), decision (hooks.v1.json authoritative,
render-user-hooks.py merge), consequences (live edits ephemeral, v1
naming for future schema bumps).

## Tradeoffs
An ADR freezes the policy; if the CLI later gains a native hooks file
import, the ADR must be superseded rather than silently contradicted.

## Verification
ADR file exists, status Accepted, and TOOLS-MAP:134 links to it.
