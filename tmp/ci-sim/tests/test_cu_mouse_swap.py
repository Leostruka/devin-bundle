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

        def press(self, b):
            sent.append(("press", b))

        def release(self, b):
            sent.append(("release", b))

    class FakeKey:
        def __getattr__(self, name):
            return name

    kb_mod = types.ModuleType("pynput.keyboard")
    kb_mod.Key = FakeKey()
    kb_mod.KeyCode = FakeKey()
    kb_mod.Controller = lambda: type(
        "K", (), {"release": lambda s, k: None})()
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


@pytest.fixture
def fake_pynput(monkeypatch):
    """Records pynput mouse press/release calls; minimal keyboard stub."""
    sent = []

    class Ctrl:
        def press(self, b):
            sent.append(("press", b))

        def release(self, b):
            sent.append(("release", b))

    class FakeKey:
        def __getattr__(self, name):
            return name

    kb_mod = types.ModuleType("pynput.keyboard")
    kb_mod.Key = FakeKey()
    kb_mod.KeyCode = FakeKey()
    kb_mod.Controller = lambda: type(
        "K", (), {"release": lambda s, k: None})()
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
    return sent


def test_emergency_release_skips_unheld_buttons(monkeypatch, fake_pynput):
    """A stray WM_RBUTTONUP fires WM_CONTEXTMENU even with no prior DOWN —
    no phantom releases when the OS reports nothing held."""
    monkeypatch.setattr(cu_actions, "_async_key_down", lambda vk: False)
    cu_actions.emergency_release()
    assert fake_pynput == []


def test_emergency_release_releases_only_held(monkeypatch, fake_pynput):
    state = {0x01: False, 0x02: True, 0x04: False}
    monkeypatch.setattr(cu_actions, "_async_key_down", state.get)
    cu_actions.emergency_release()
    assert fake_pynput == [("release", "R")]


def test_emergency_release_unqueryable_releases_all(monkeypatch, fake_pynput):
    """Dead-worker cleanup must still work when state can't be read."""
    monkeypatch.setattr(cu_actions, "_async_key_down", lambda vk: None)
    cu_actions.emergency_release()
    assert fake_pynput == [("release", "L"), ("release", "R"),
                           ("release", "M")]


def test_emergency_release_swap_maps_physical_vks(monkeypatch, fake_pynput):
    """On swapped hosts physical-left-held surfaces under VK_RBUTTON."""
    monkeypatch.setattr(cu_actions, "_swap_state", True)
    state = {0x01: False, 0x02: True, 0x04: False}
    monkeypatch.setattr(cu_actions, "_async_key_down", state.get)
    cu_actions.emergency_release()
    assert fake_pynput == [("release", "L")]


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
