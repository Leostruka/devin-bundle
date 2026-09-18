# 11 — iframe/shadow context scoping

**Intent:** elements inside iframes/shadow roots are distinct namespaces —
selectors must not silently hit the wrong context.

**What to build:** context-scoped resolution: `BrowserClient.evaluate`
accepts a context path (CDP: frame/sessionId; BiDi: context id). Selector
API requires explicit context when target is nested; ambiguous bare
selectors that match in multiple contexts -> typed reject, not first-match.

**Proposed modules:** `cu_browser.py` (+fixture page with iframe + shadow
DOM containing duplicate selectors).

**Estimated size (lines):** ~110 + ~80 tests

**Input / Output:** (selector, context_path) -> unique element or reject

**Blocked by:** 09

**Gate:** `python -m pytest tests/test_cu_context_scope.py -q` + live fixture

**Expect:** duplicate selectors across contexts -> reject; explicit context
path resolves the right one

**Evidence:** pytest + fixture output

**Status:** resolved

- [ ] iframe context isolated from parent document
- [ ] shadow root needs explicit path, never pierced implicitly
- [ ] ambiguous match -> typed reject

## Answer

`evaluate_in(expr, context)` scopes BiDi eval per browsingContext; CDP rejects
foreign contexts explicitly (frame sessions out of scope). `contexts()` lists
the BiDi tree. Evidence: routing tests.
