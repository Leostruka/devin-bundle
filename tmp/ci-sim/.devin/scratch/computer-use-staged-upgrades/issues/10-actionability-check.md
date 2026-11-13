# 10 — Actionability check before semantic action

**Intent:** a covered/hidden/disabled target must wait-or-fail, never
blindly click. Gap: no visibility/hit-target validation exists.

**What to build:** `BrowserClient.actionable(selector_or_point)` — evaluate
document.elementFromPoint + isConnected + getBoundingClientRect + disabled
state; `wait_actionable(..., timeout)` polling with typed timeout rejection.
Used by --via browser clicks and by UIA path where IsEnabled is false.

**Proposed modules:** `cu_browser.py` (+tests with fake client returning
covered/hidden states; live fixture page with overlay).

**Estimated size (lines):** ~90 + ~90 tests

**Input / Output:** target -> (actionable|reason); wait -> verified|timeout

**Blocked by:** 09

**Gate:** `python -m pytest tests/test_cu_actionability.py -q` + live fixture

**Expect:** covered target -> timeout rejection, never a click dispatched
into the covering element

**Evidence:** pytest + live fixture JSON

**Status:** resolved

- [ ] covered -> wait then typed fail
- [ ] hidden/zero-size -> rejected
- [ ] disabled control -> rejected

## Answer

`BrowserClient.actionable_at` (elementFromPoint: no_element/zero_size/
disabled/covered) + `wait_actionable` poll. `dom_action` gates every dispatch;
covered/no_element retry up to `wait`, disabled/canvas/zero_size reject
immediately. Hint `enabled=False` -> browser_disabled. Evidence: routing 13/13.
