# 09 — Browser action routing (`--via browser`)

**Intent:** semantic browser actions only reach bound browsers; everything
else keeps the visual/physical path. Gap: BrowserClient exists but nothing
routes to it.

**What to build:** `cu_actions.route(hwnd)` — resolves element hwnd -> pid,
`cu_browser.check(hwnd)` must pass, returns client or typed reject. `mouse.py
click --via browser` and `type_text.py --via browser` route through it;
unbound/foreign -> reject before any dispatch, zero physical fallback.

**Proposed modules:** `cu_actions.py`, `mouse.py`, `type_text.py` (+tests).

**Estimated size (lines):** ~120 + ~80 tests

**Input / Output:** `--via browser` flag -> JSON result with
`dispatch.backend: "dom"` or typed rejection

**Blocked by:** none (04 landed)

**Gate:** `python -m pytest tests/test_cu_browser_routing.py -q`

**Expect:** bound hwnd -> client dispatch; unbound/foreign/expired -> reject,
zero input calls

**Evidence:** pytest output

**Status:** resolved

- [ ] unbound browser never receives CDP/BiDi calls
- [ ] foreign-process hwnd rejected before dispatch
- [ ] visual path untouched when --via not given

## Answer

`--via browser` landed: `dom_action` (check->client->css convert->click/type),
auto prefers DOM only when bound, unbound/foreign reject pre-dispatch, hint
rejection now precedes pynput import. Evidence: `test_cu_browser_routing.py`
7/7 + contract 12/12.
