# Issue 02: OpenUI Lang adoption

Status: DSL spec in `.devin/rts/openui-lang.md` and local parser/renderer
implemented in `extensions/craft-bridge/ui_dsl.py` (DSL v1). External
adapter remains future work.

## Scope

- Line-based DSL (one UI element per line) replacing nested JSON for
  streamed HUDs and interactive grilling forms.
- Implemented: strict `parse`/`emit` round-trip, `StreamParser` for
  incremental feeds (partial lines never render), `render_html` escaped
  fragment with a non-modal `<dialog open>` ancestor + `method="dialog"`
  form and `role="progressbar"` bars, `benchmark` with a real BPE
  tokenizer.
- Measured: ratio 0.5654 vs minified JSON on the shipped fixture
  (`extensions/craft-bridge/benchmark-results.json`, `Xenova/gpt-4`).
  The ~50% target was NOT met on this fixture - not a universal claim.
- Browser smoke relocated outside the repo to
  `devin-cache/openui-browser` (pytest 1 pass).
- `extensions/craft-bridge/`: adapter prerequisite still holds - no
  `ops_map.json` entry until an external app is verified to accept the
  DSL. The bridge dispatches app commands, not UI elements.

## Non-goals

No breaking change to existing ops; no new runtime deps in `scripts/`;
no spark-view integration shipped.
