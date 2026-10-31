# Issue 02: OpenUI Lang adoption

Status: DSL spec landed in `.devin/rts/openui-lang.md`; craft-bridge op is
future work.

## Scope

- Line-based DSL (one UI element per line) replacing nested JSON for
  streamed HUDs and interactive grilling forms. Target: ~half the token
  cost for the same semantics.
- Grammar + examples live in `.devin/rts/openui-lang.md`.
- `extensions/craft-bridge/`: new op in `ops_map.json` emitting DSL; JSON
  stays the default renderer until the DSL path has round-trip tests.

## Non-goals

No breaking change to existing ops; no new runtime deps.
