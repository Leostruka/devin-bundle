# OpenUI Lang (line-based UI DSL)

Implemented local pattern: a strict, versioned one-element-per-line DSL for
streamed HUDs and interactive grilling forms, implemented in
`extensions/craft-bridge/ui_dsl.py` (`DSL_VERSION = 1`). Local capability
only - no claim of upstream OpenUI grammar compatibility and no external
app contract. The craft bridge still dispatches only real app CLI commands.

## Grammar (v1)

```
# comment
hud title="Quest Tracker" anchor=top-right
row label="Kills" value=12 of=20
bar value=0.6 color=green
end
form id=grill-3 title="Confirm scope"
q choice id=q1 text="Delete cache?" options=yes|no|skip
q multi id=q2 text="Targets" options=docs|code|tests
btn action=submit label="Go"
end
```

Strict rules (violations raise `ParseError`):

- One element per line; `end` closes the nearest open block (`hud`, `form`);
  no nesting; blocks must contain at least one child.
- Attributes are `key=value` separated by single spaces; values are bare
  tokens or double-quoted with `\\` and `\"` escapes only; no duplicates.
- `kind` is a reserved qualifier for `q` (`choice` | `multi`), not an
  attribute. `id` values match `[A-Za-z][A-Za-z0-9_-]*`, are unique
  document-wide; `options` are `|`-separated and may not repeat.
- Bounds: `MAX_LINES 2000`, `MAX_BYTES 128 KiB`, `MAX_LINE_LEN 1024`,
  `MAX_ELEMENTS 500`, `MAX_VALUE_LEN 512`, `MAX_OPTIONS 64`.
- Children restricted per parent: `hud` -> `row`/`bar`; `form` -> `q`/`btn`.
- `row` value/of numeric; `bar` value in [0,1]; `btn action` a lowercase
  token.

## API and CLI

- `parse(text) -> Document`; `emit(doc)` round-trips canonical input.
- `StreamParser.feed(str|bytes)` validates each completed line as it
  arrives; `snapshot()` never includes a partial last line.
- `render_html(doc)` emits a self-contained, escaped HTML fragment - no
  scripts, no URLs. Each `form` block renders inside a non-modal
  `<dialog open>` ancestor with a `method="dialog"` `<form>`, so native
  submit closes the dialog in-page (no endpoint, no JS). `bar` renders a
  real `role="progressbar"` element with `aria-valuemin/max/now` and
  `aria-label` (native visible progress). A browser smoke run was
  relocated outside the repo (`devin-cache/openui-browser`, pytest 1
  pass).
- `benchmark(dsl_src, tokenizer=None)` counts DSL tokens vs the minified
  semantic-equivalent JSON payload with a real BPE tokenizer
  (`Xenova/gpt-4`, fallback `Xenova/cl100k_base`; a local `tokenizer.json`
  path is accepted and recorded with sha256).

```
python ui_dsl.py parse --input in.dsl [--output out.dsl] [--force]
python ui_dsl.py render --input in.dsl --output out.html [--force]
python ui_dsl.py benchmark --fixture in.dsl [--tokenizer PATH_OR_ID] [--output res.json]
```

## Measured benchmark (fixture-specific, not a universal claim)

`extensions/craft-bridge/benchmark-results.json` on the shipped fixture:
`Xenova/gpt-4`, minified JSON comparison, `dsl_tokens=108` vs
`json_tokens=191` -> ratio **0.5654**. The ~50% target was NOT met on
this fixture; the result is one fixture and one tokenizer, not a
universal savings claim.

## Adoption map

| Surface | Change |
|---|---|
| `extensions/craft-bridge/` | Parser/renderer shipped in `ui_dsl.py`. Still no `ops_map.json` entry: the bridge dispatches external CLI commands, and no external app is verified to accept this DSL. |
| Grilling forms | `ask_user_question` payloads stay native; DSL covers custom HUD/form surfaces only. |
| `spark-view` (craft-bridge) | Renderer support unverified; incremental consumption via `StreamParser` exists locally but no spark-view integration is shipped. |

## Non-goals

No breaking change to existing craft-bridge ops; no new runtime deps in
`scripts/`; no layout engine (renderer decides geometry); no claim that any
external Katana/Seedance-style service consumes this DSL.
