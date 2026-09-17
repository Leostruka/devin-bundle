# 12 — Canvas/graphics -> visual fallback

**Intent:** canvas has no DOM targets — semantic path must hand off to the
visual path explicitly, never guess.

**What to build:** target classifier: DOM-actionable | canvas/graphics |
unknown. canvas -> route to screenshot+physical input path with
`fallback: "visual"` in the result; unknown -> same. Wired into the 09
router so --via auto/browser degrades honestly.

**Proposed modules:** `cu_browser.py`, `cu_actions.py` (+fixture: canvas
element; tests assert fallback flag).

**Estimated size (lines):** ~70 + ~60 tests

**Input / Output:** classified target -> semantic action OR visual fallback
with declared backend

**Blocked by:** 09

**Gate:** `python -m pytest tests/test_cu_canvas_fallback.py -q`

**Expect:** canvas target -> result carries dispatch.backend "physical" +
fallback reason; zero DOM calls on it

**Evidence:** pytest output

**Status:** resolved

- [ ] canvas never receives semantic calls
- [ ] fallback is declared in output, not silent

## Answer

actionable_at returns reason "canvas" for CANVAS/VIDEO hits; `auto` path records
`dispatch.dom_fallback` and falls through to UIA/physical; explicit
`--via browser` rejects. Evidence: test_canvas_hit_rejects_dom.
