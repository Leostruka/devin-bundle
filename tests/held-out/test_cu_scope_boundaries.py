"""F3 S9 held-out - scoped-channel boundary checks.

Two deterministic axes, plus one documented manual gate:

1. Static: cu_scope.py / cu_overlay.py never reference global-input APIs
   (SendInput, InputInjector, journal hooks, keybd_event, focus theft).
   PostMessageW / WriteConsoleInput / UIA patterns / CDP are the allowed
   scoped mechanisms.
2. Dynamic: host-input modules are replaced by exploding traps; scoped
   dispatch on a fake Win32 tree must complete without touching them.
   PostMessageW delivery to the target HWND is asserted on the fake.

MANUAL GATE (human required): with Notepad open and NOT focused, run
    python extensions/computer-use/type_text.py "agent-typed" --channel scope --title Notepad
while a human types into an unrelated focused window. Expectation:
the scoped text appears in Notepad's buffer (delivery, possibly echoed)
and the human's keystrokes land only in their window. Real cursor
position must not move (ghost overlay is a separate sprite).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cu_load import load  # noqa: E402

EXT = Path(__file__).resolve().parents[2] / \
    "extensions" / "computer-use"

SCOPED_MODULES = ["cu_scope.py", "cu_overlay.py"]

# Global-input APIs that must never appear in scoped-path code.
FORBIDDEN_TOKENS = ("SendInput", "InputInjector", "SetWindowsHookEx",
                    "SetWinEventHook", "keybd_event", "JournalRecord",
                    "SetForegroundWindow", "AllowSetForegroundWindow",
                    "GetAsyncKeyState", "BlockInput", "pynput")


def _code_tokens(path):
    import io
    import tokenize
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(path.read_text("utf-8")).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


@pytest.mark.parametrize("mod", SCOPED_MODULES)
def test_scoped_module_has_no_global_input_api(mod):
    code = _code_tokens(EXT / mod)
    for tok in FORBIDDEN_TOKENS:
        assert tok not in code, f"{mod} references {tok}"


class Exploding:
    """Any attribute access on this module-stand-in is a leak."""

    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        raise AssertionError(
            f"scoped path touched host module {self._name}.{attr}")


@pytest.fixture
def host_traps(monkeypatch):
    for name in ("pynput", "pyautogui", "keyboard"):
        monkeypatch.setitem(sys.modules, name, Exploding(name))
    yield


class FakeWin:
    """HWND tree: frame 0x64 -> Edit child 0x65 (Notepad shape)."""

    def __init__(self):
        self.posted = []
        import ctypes
        self.u32 = self
        self._pt = ctypes.wintypes.POINT()

    def PostMessageW(self, hwnd, msg, wp, lp):
        self.posted.append((hwnd, msg, wp, lp))
        return 1

    def ScreenToClient(self, hwnd, pt):
        pt._obj.x -= 100  # frame at (100, 200); pt is byref-wrapped
        pt._obj.y -= 200
        return 1

    def class_name(self, hwnd):
        return {0x64: "Notepad", 0x65: "Edit"}.get(hwnd, "")

    def enum_children(self, hwnd):
        return [0x65] if hwnd == 0x64 else []

    def title(self, hwnd):
        return "Untitled - Notepad"

    def pid(self, hwnd):
        return 4242

    def visible(self, hwnd):
        return True

    def rect(self, hwnd):
        return (100, 200, 500, 400)


def _fake_win(monkeypatch):
    import cu_scope
    w = FakeWin()
    monkeypatch.setattr(cu_scope, "win", w)
    return w


def test_scoped_click_posts_to_child_only(host_traps, monkeypatch,
                                          capsys):
    """Scoped click = PostMessage to the input HWND; host input modules
    would explode if touched."""
    w = _fake_win(monkeypatch)
    mouse = load("mouse")
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "click", "150", "250",
                         "--channel", "scope", "--hwnd", "0x64"])
    mouse.main()
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["delivered"] is True
    assert out["hwnd"] == 0x65  # Edit child, not the frame
    msgs = [m[1] for m in w.posted]
    assert msgs == [0x0201, 0x0202]  # WM_LBUTTONDOWN/UP only
    assert all(m[0] == 0x65 for m in w.posted)  # nothing to the frame


def test_scoped_type_posts_wm_char(host_traps, monkeypatch, capsys):
    w = _fake_win(monkeypatch)
    type_text = load("type_text")
    monkeypatch.setattr(sys, "argv",
                        ["type_text.py", "hi", "--channel", "scope",
                         "--hwnd", "0x64"])
    type_text.main()
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert w.posted == [(0x65, 0x0102, ord("h"), 0),
                        (0x65, 0x0102, ord("i"), 0)]


def test_scoped_never_falls_back_to_host(host_traps, monkeypatch,
                                         capsys):
    """A failed delivery must report honestly - no silent host retry."""
    w = _fake_win(monkeypatch)
    w.PostMessageW = lambda *a: 0  # delivery fails
    type_text = load("type_text")
    monkeypatch.setattr(sys, "argv",
                        ["type_text.py", "hi", "--channel", "scope",
                         "--hwnd", "0x64"])
    with pytest.raises(SystemExit) as ei:
        type_text.main()
    out = json.loads(capsys.readouterr().out)
    assert ei.value.code == 1
    assert out["ok"] is False and out["delivered"] == 0
