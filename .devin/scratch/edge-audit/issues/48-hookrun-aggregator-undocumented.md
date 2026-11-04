# 48 -- _hookrun aggregation layer has no documentation

- **Status**: open
- **Category**: documentation
- **Severity**: P2
- **File**: scripts/_hookrun.py

## Evidence
`scripts/_hookrun.py` implements the merge semantics for the consolidated
hook entry points (referenced by `pre-exec-guard.py:6` "see _hookrun.py
for merge rules"). Nothing outside the file itself documents: how
multiple inner-script decisions merge (block precedence, reason
aggregation), whether a failing inner script short-circuits or is
fail-open, ordering guarantees, or timeout budgeting across the 90s/300s
hook timeouts now shared by many scripts. `ARCHITECTURE_MANIFEST.md:41-43`
describes fail-open/fail-closed policy per hook but not the aggregation
contract. This is the single most load-bearing piece of the hooks
subsystem and the least discoverable.

## Recommendation
Add a `## Hook aggregation` section to TOOLS-MAP (or a short
`.devin/docs/HOOKS-PIPELINE.md`) covering event -> entry point -> inner
script list -> merge rules -> exit-code mapping, mirroring the docstring
of `_hookrun.py`.

## Verification
New doc lists every aggregator and its inner list; spot-check three
against `ALWAYS`/`TEXT_ONLY` constants and `_hookrun.main(...)` calls.
