# CU Mouse Swap + Stdout JSON Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use /dispatching-parallel-agents (recommended) or /executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `mouse.py click --button left` must mean the semantic *primary* click even on left-handed Windows hosts (SM_SWAPBUTTON), and every computer-use CLI must emit exactly one JSON object on stdout even when it crashes.

**Architecture:** Logical→physical button translation lives in `cu_actions` (already the shared action/result contract module). `resolve_button(Button, name)` queries `GetSystemMetrics(23)` once (cached), swapping left↔right at the pynput dispatch seam — transparent to callers. `run_cli(main)` wraps each `__main__` entry so unhandled exceptions still print `{"ok": false, "error": ...}`.

**Tech Stack:** Python 3 stdlib only (`ctypes` for SM_SWAPBUTTON — no new deps), pynput (existing), pytest + `tests/cu_load.py` module loader + `unittest.mock`/`monkeypatch`.

## Global Constraints

- No new third-party dependencies — swap detection uses `ctypes.windll.user32.GetSystemMetrics(23)` only.
- Never reconfigure the user's OS — translation is logical, at dispatch time only.
- stdout contract: exactly one JSON object per invocation; `ok:false` on failure.
- No AI signatures or `Co-Authored-By` trailers in commits.
- DOM path (`cu_browser` CDP `cli.click`) needs no translation — CDP buttons are already logical.
- `cu_hints.py` has no `__main__`; its CLI surface is `screenshot.py --hints` — the guard lives at the entry points.
- Gates ledger: `.devin/ledgers/cu-button-swap-json-guard.md` — fill EVIDENCE per gate.

## Proposed Modules and Interfaces

- `extensions/computer-use/cu_actions.py` — add:
  - `_SM_SWAPBUTTON = 23`
  - `_get_system_metrics(index) -> int` — 0 off-Windows / on error
  - `buttons_swapped() -> bool` — cached result of `_get_system_metrics(23)`
  - `resolve_button(Button, name) -> Button` — logical name → physical constant
  - `run_cli(main) -> None` — entry-point guard
- `extensions/computer-use/mouse.py` — click + drag dispatch via `resolve_button`; `__main__` via `run_cli`
- `extensions/computer-use/screenshot.py` — `__main__` via `run_cli`
- `extensions/computer-use/type_text.py` — `__main__` via `run_cli`
- `tests/test_cu_mouse_swap.py` — new test file (living)
- `.devin/ledgers/cu-button-swap-json-guard.md` — gates ledger (living)

---

### Task 1: Primary/secondary click survives SM_SWAPBUTTON

**Files:**
- Modify: `extensions/computer-use/cu_actions.py` (imports + new functions at end)
- Modify: `extensions/computer-use/mouse.py:253` (click), `mouse.py:304-332` (drag)
- Test: `tests/test_cu_mouse_swap.py` (create)

**Interfaces:**
- Produces: `cu_actions.resolve_button(Button, name)`, `cu_actions.buttons_swapped()`
- Consumed by: `mouse.py` click (`args.button`) and drag (`"left"`)

- [ ] **Step 1: Write the failing test**

Create `tests/test_cu_mouse_swap.py`:

```python
"""SM_SWAPBUTTON: logical button names translate to physical constants at
the pynput seam — 'left' always means the semantic primary click."""
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load

cu_actions = load("cu_actions")


class FakeButton:
    left = "L"
    right = "R"
    middle = "M"


@pytest.fixture(autouse=True)
def _reset_swap_cache(monkeypatch):
    monkeypatch.setattr(cu_actions, "_swap_state", None)


def test_resolve_button_identity_without_swap(monkeypatch):
    monkeypatch.setattr(cu_actions, "_get_system_metrics", lambda i: 0)
    assert cu_actions.resolve_button(FakeButton, "left") == "L"
    assert cu_actions.resolve_button(FakeButton, "right") == "R"
    assert cu_actions.resolve_button(FakeButton, "middle") == "M"


def test_resolve_button_swapped(monkeypatch):
    monkeypatch.setattr(cu_actions, "_get_system_metrics", lambda i: 1)
    assert cu_actions.resolve_button(FakeButton, "left") == "R"
    assert cu_actions.resolve_button(FakeButton, "right") == "L"
    assert cu_actions.resolve_button(FakeButton, "middle") == "M"


def test_click_dispatches_swapped_button(monkeypatch, capsys):
    """mouse.py click --button left under SM_SWAPBUTTON: pynput receives
    the RIGHT physical constant so the OS delivers a primary click."""
    sent = []

    class Ctrl:
        position = (0, 0)
        def press(self, b): sent.append(("press", b))
        def release(self, b): sent.append(("release", b))

    class FakeKey:
        def __getattr__(self, name): return name

    kb_mod = types.ModuleType("pynput.keyboard")
    kb_mod.Key = FakeKey()
    kb_mod.KeyCode = FakeKey()
    kb_mod.Controller = lambda: type("K", (), {"release": lambda s, k: None})()
    ms_mod = types.ModuleType("pynput.mouse")
    ms_mod.Button = FakeButton
    ctrl = Ctrl()
    ms_mod.Controller = lambda: ctrl
    pkg = types.ModuleType("pynput")
    pkg.mouse = ms_mod
    pkg.keyboard = kb_mod
    monkeypatch.setitem(sys.modules, "pynput", pkg)
    monkeypatch.setitem(sys.modules, "pynput.mouse", ms_mod)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", kb_mod)
    monkeypatch.setattr(cu_actions, "_swap_state", True)
    monkeypatch.delenv("CU_SESSION", raising=False)
    mouse = load("mouse")
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "click", "10", "20", "--button", "left",
                         "--profile", "fast"])
    mouse.main()
    assert sent == [("press", "R"), ("release", "R")]
    assert json.loads(capsys.readouterr().out)["ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cu_mouse_swap.py -v`
Expected: FAIL — `AttributeError: module 'cu_actions' has no attribute '_swap_state'` (or `resolve_button`)

- [ ] **Step 3: Implement the swap translation in `cu_actions.py`**

Change the import line and append:

```python
import json
import os
import sys
import time
```

```python
_SM_SWAPBUTTON = 23
_swap_state = None


def _get_system_metrics(index):
    """user32.GetSystemMetrics(index); 0 off-Windows or on any failure."""
    if os.name != "nt":
        return 0
    try:
        import ctypes
        return ctypes.windll.user32.GetSystemMetrics(index)
    except Exception:
        return 0


def buttons_swapped():
    """True when the OS reports swapped primary/secondary buttons
    (SM_SWAPBUTTON=23). Cached: the setting requires re-login to change."""
    global _swap_state
    if _swap_state is None:
        _swap_state = bool(_get_system_metrics(_SM_SWAPBUTTON))
    return _swap_state


def resolve_button(Button, name):
    """Logical button name -> physical pynput Button constant.

    pynput's Button.left emits MOUSEEVENTFLEFTDOWN, which Windows routes
    through SM_SWAPBUTTON — on a left-handed host that event IS the
    secondary click. Swap left<->right at dispatch so the caller's
    semantic 'left' stays the primary action; middle never swaps."""
    if buttons_swapped() and name in ("left", "right"):
        name = "right" if name == "left" else "left"
    return getattr(Button, name)
```

- [ ] **Step 4: Wire `resolve_button` into `mouse.py`**

Click path — replace line 253:

```python
btn = getattr(Button, args.button)
```

with:

```python
btn = cu_actions.resolve_button(Button, args.button)
```

Drag path — both `owned.press(mouse, Button.left)` / `owned.release(mouse, Button.left)` pairs (fast branch ~lines 314-322, profiled branch ~lines 326-332) take a resolved button. Before the `with cu_actions.OwnedInputs() as owned:` block add:

```python
drag_btn = cu_actions.resolve_button(Button, "left")
```

and replace the four `Button.left` uses inside the drag block with `drag_btn`.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_cu_mouse_swap.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add extensions/computer-use/cu_actions.py extensions/computer-use/mouse.py tests/test_cu_mouse_swap.py
git commit -m "fix(computer-use): translate logical mouse buttons under SM_SWAPBUTTON"
```

---

### Task 2: Stdout JSON survives any CLI crash

**Files:**
- Modify: `extensions/computer-use/cu_actions.py` (append `run_cli`)
- Modify: `extensions/computer-use/screenshot.py:271-272` (`__main__`)
- Modify: `extensions/computer-use/mouse.py:348-349` (`__main__`)
- Modify: `extensions/computer-use/type_text.py:264-265` (`__main__`)
- Test: `tests/test_cu_mouse_swap.py` (extend)

**Interfaces:**
- Produces: `cu_actions.run_cli(main) -> None`
- Consumed by: the three `if __name__ == "__main__"` blocks

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_cu_mouse_swap.py`:

```python
def test_run_cli_emits_json_on_crash(capsys):
    def boom():
        raise RuntimeError("uia exploded")
    with pytest.raises(SystemExit):
        cu_actions.run_cli(boom)
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and "uia exploded" in out["error"]


def test_run_cli_reraises_system_exit(capsys):
    """fail()/usage exits must pass through untouched — single JSON."""
    def exits():
        print(json.dumps({"ok": False, "error": "usage: bad flag"}))
        sys.exit(2)
    with pytest.raises(SystemExit) as ei:
        cu_actions.run_cli(exits)
    assert ei.value.code == 2
    out = capsys.readouterr().out
    assert json.loads(out)["ok"] is False


def test_hints_crash_path_prints_json(monkeypatch, capsys):
    """Reproduces the reported failure: enum_clickables raising inside
    screenshot.main()'s unguarded --hints block still yields one JSON."""
    screenshot = load("screenshot")
    monkeypatch.delenv("CU_SESSION", raising=False)

    def boom(scope="focused"):
        raise RuntimeError("uia provider died")
    monkeypatch.setattr(screenshot.cu_hints, "enum_clickables", boom)
    monkeypatch.setattr(
        sys, "argv",
        ["screenshot.py", "--hints", "--no-image", "--window", "all"])
    with pytest.raises(SystemExit):
        cu_actions.run_cli(screenshot.main)
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and "uia provider died" in out["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_cu_mouse_swap.py -k "run_cli or hints_crash" -v`
Expected: FAIL — `AttributeError: module 'cu_actions' has no attribute 'run_cli'`; the crash test fails with the raw `RuntimeError` escaping instead of `SystemExit`.

- [ ] **Step 3: Implement `run_cli` in `cu_actions.py`**

Append:

```python
def run_cli(main):
    """Entry-point guard for the stdout JSON contract: an unhandled crash
    still emits exactly one {"ok": false} object so a downstream
    json.loads(sys.stdin) never sees a traceback. SystemExit (fail/usage
    paths) re-raises untouched — those paths already printed their JSON."""
    try:
        main()
    except SystemExit:
        raise
    except BaseException as e:
        print(json.dumps({"ok": False,
                          "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
```

- [ ] **Step 4: Wrap the three `__main__` entry points**

`screenshot.py` — add `import cu_actions` alongside the other `cu_*` imports at the top, and change the end of file to:

```python
if __name__ == "__main__":
    cu_actions.run_cli(main)
```

`mouse.py` end of file — same replacement (it already imports `cu_actions`).

`type_text.py` end of file — same replacement (already imports `cu_actions`).

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_cu_mouse_swap.py -v`
Expected: all passed (6 tests)

- [ ] **Step 6: Commit**

```bash
git add extensions/computer-use/cu_actions.py extensions/computer-use/screenshot.py extensions/computer-use/mouse.py extensions/computer-use/type_text.py tests/test_cu_mouse_swap.py
git commit -m "fix(computer-use): guard CLI entry points so stdout stays single-JSON on crash"
```

---

### Task 3: Full-suite verification + ledger evidence

**Files:**
- Modify: `.devin/ledgers/cu-button-swap-json-guard.md` (fill EVIDENCE lines)

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest tests -q`
Expected: all tests pass (422 collected pre-change + 6 new; no deletions, no skips introduced)

- [ ] **Step 2: Smoke the real CLI**

Run (extension venv python): `screenshot.py --hints --no-image --window all` and `mouse.py position`
Expected: stdout is exactly one parseable JSON object each.

- [ ] **Step 3: Fill the ledger**

Update every `EVIDENCE: pending` line in `.devin/ledgers/cu-button-swap-json-guard.md` with the observed output snippet.

- [ ] **Step 4: Commit ledger**

```bash
git add .devin/ledgers/cu-button-swap-json-guard.md .devin/plans/2026-09-18-cu-button-swap-json-guard.md
git commit -m "chore(computer-use): gates ledger for button-swap + JSON guard"
```
