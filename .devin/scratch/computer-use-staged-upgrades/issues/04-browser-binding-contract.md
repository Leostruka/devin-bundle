# 04 — Browser binding contract `cu_browser`

**Intent:** DOM/ARIA/CDP only ever against an explicitly-bound test browser;
never auto-enable remote debugging on a personal session.

**What to build:** `extensions/computer-use/cu_browser.py` — `bind(endpoint,
pid)` writes `<temp>/devin-cu-browser.json` {endpoint, pid, session_id,
created_at}; `unbind()`; `binding()`; `check(hwnd) -> (allowed, reason)`
matching element hwnd->pid against the bound pid with TTL+session rules like
hints. `_cdp_client()` seam returns None unless an approved driver is present
(honest "unavailable", not silent). `tests/test_cu_browser_contract.py` with
fake client: unbound origin rejected, wrong pid rejected, stale binding
expired, CSS-vs-physical transform documented.

**Proposed modules:** new `cu_browser.py` (+test). No new deps — CDP client
stays a seam until a driver is approved.

**Estimated size (lines):** ~130 + ~110 tests

**Input / Output:** bind/unbind/check → JSON-safe dicts / (allowed, reason)

**Blocked by:** None — can start immediately.

**Gate:** `python -m pytest tests/test_cu_browser_contract.py -q`

**Expect:** exit 0; unbound/foreign/expired bindings all reject

**Evidence:** pytest output

**Status:** resolved

- [ ] no auto-enable of remote debugging anywhere
- [ ] binding is session+TTL bound like hints
- [ ] CSS viewport vs desktop pixels never mixed

## Answer

`cu_browser.py` landed: loopback-only bind, pid check via
GetWindowThreadProcessId, session+TTL like hints, `_cdp_client()` returns
None until a driver is approved, explicit CSS->desktop px conversion.
Evidence: `test_cu_browser_contract.py` 12/12.
