# 46 -- TOOLS-MAP hook table describes pre-consolidation wiring

- **Status**: resolved
- **Category**: documentation
- **Severity**: P2
- **File**: .devin/docs/TOOLS-MAP.md:82-110

## Evidence
The "Hooks (8 eventos, 21 scripts)" table lists each guard script bound to
its own matcher (e.g. `validate-mermaid.py` at `^(write|edit)$`,
`destructive-gate.py` at `^exec$`). `hooks.v1.json` actually wires only 10
entry points: `pre-exec-guard.py`, `pre-write-guard.py`, `post-exec.py`,
`memory-post-edit.py`, `compact-gate.py`, `constraint-pinning.py`,
`user-prompt.py`, `session-start.py`, `stop-guard.py`, `memory-stop.py`.
The named scripts now run inside aggregators via `scripts/_hookrun.py`
(e.g. `pre-write-guard.py` ALWAYS list runs `architecture-gate.py`,
`validate-tool-args.py`, `no-em-dash.py`; TEXT_ONLY adds
`check-ai-signature.py` and `validate-mermaid.py`). The documented
matchers are also wrong post-consolidation (`notebook_edit` is now
matched by `pre-write-guard`). A reader debugging hook behavior will look
for bindings that no longer exist.

## Recommendation
Rewrite the table to show the two layers: hooks.v1.json entry point ->
aggregator -> inner scripts, with per-script notes preserved. Add a line
stating inner scripts are never bound directly.

## Verification
Diff the table against `python -c "import json;print(json.load(open('hooks.v1.json')))"`
and each aggregator's script list; every row should resolve.

## Answer

Rewrote the TOOLS-MAP hook table to the post-consolidation reality: 10 entry points in hooks.v1.json mapped to their inner-script lists (verified against each aggregator source), matchers corrected (`notebook_edit` under pre-write-guard), explicit rule that inner scripts are never bound directly.
