# OpenUI Lang (line-based UI DSL)

Proposed pattern: a linear, one-element-per-line DSL for streamed HUDs and
interactive grilling forms. Target: half the tokens of equivalent nested
JSON, to be measured with a fixed tokenizer and equivalent fixtures.
Renderer implementation remains future work; this is a local sketch,
not a claim of upstream OpenUI grammar compatibility.

## Grammar (v0 sketch)

```
# comment
hud title="Quest Tracker" anchor=top-right
row label="Kills" value=12 of=20
bar value=0.6 color=green
form id=grill-3 title="Confirm scope"
q choice id=q1 text="Delete cache?" options=yes|no|skip
q multi id=q2 text="Targets" options=docs|code|tests
btn action=submit label="Go"
end
```

Rules:

- One element per line; `end` closes the nearest open block (`hud`, `form`).
- Attributes are `key=value`, values quoted only when they contain spaces.
- Streaming: each flushed line is renderable; a partial last line is ignored
  until completed.
- Round-trip: `emit(parse(lines)) == lines` for canonical input.

## Adoption map

| Surface | Change |
|---|---|
| `extensions/craft-bridge/` | New `ops_map.json` op emitting DSL; JSON renderer stays default until round-trip tests exist (`tests/validation/`). |
| Grilling forms | `ask_user_question` payloads stay native; DSL covers custom HUD/form surfaces only. |
| `spark-view` (craft-bridge) | Incremental renderer consumes the line stream. |

## Non-goals

No breaking change to existing craft-bridge ops; no new runtime deps; no
layout engine (renderer decides geometry).
