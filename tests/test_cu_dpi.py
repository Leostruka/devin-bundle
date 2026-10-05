"""cu_dpi.py unit tests — ctypes calls faked; runs on any platform."""
import ctypes
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cu_load  # noqa: E402


def _load(monkeypatch, plat="win32"):
    monkeypatch.setattr(sys, "platform", plat, raising=False)
    return cu_load.load("cu_dpi")


def _ctxval(ctx):
    return ctypes.c_ssize_t(ctx.value).value


def test_set_awareness_prefers_pmav2(monkeypatch):
    d = _load(monkeypatch)
    calls = []

    class U32:
        def SetProcessDpiAwarenessContext(self, ctx):
            calls.append(("ctx", _ctxval(ctx)))
            return True

    class Shcore:
        def SetProcessDpiAwareness(self, a):
            calls.append(("awareness", a))
            return 0

    monkeypatch.setattr(ctypes, "windll",
                        types.SimpleNamespace(user32=U32(), shcore=Shcore()))
    assert d.set_dpi_awareness() == "pmv2"
    assert calls == [("ctx", -4)]


def test_set_awareness_fallback_to_v1(monkeypatch):
    d = _load(monkeypatch)
    calls = []

    class U32:
        def SetProcessDpiAwarenessContext(self, ctx):
            calls.append(("ctx", _ctxval(ctx)))
            raise OSError("not supported")

    class Shcore:
        def SetProcessDpiAwareness(self, a):
            calls.append(("awareness", a))
            return 0

    monkeypatch.setattr(ctypes, "windll",
                        types.SimpleNamespace(user32=U32(), shcore=Shcore()))
    assert d.set_dpi_awareness() == "shcore"
    assert calls == [("ctx", -4), ("awareness", 2)]


def test_set_awareness_noop_off_windows(monkeypatch):
    d = _load(monkeypatch, plat="linux")
    assert d.set_dpi_awareness() is None  # no ctypes access at all


def test_physical_bounds_uses_dwm(monkeypatch):
    d = _load(monkeypatch)

    class R(ctypes.Structure):
        _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                    ("r", ctypes.c_long), ("b", ctypes.c_long)]

    def fake_dwm(hwnd, attr, ptr, size):
        r = ctypes.cast(ptr, ctypes.POINTER(R)).contents
        r.l, r.t, r.r, r.b = 10, 20, 310, 220
        return 0

    class U32:
        def GetWindowRect(self, hwnd, ptr):
            r = ctypes.cast(ptr, ctypes.POINTER(R)).contents
            r.l, r.t, r.r, r.b = 2, 12, 318, 228  # inflated borders
            return True

    monkeypatch.setattr(ctypes, "windll",
                        types.SimpleNamespace(dwmapi=types.SimpleNamespace(
                            DwmGetWindowAttribute=fake_dwm), user32=U32()))
    assert d.physical_window_bounds(7) == (10, 20, 310, 220)


def test_physical_bounds_dwm_fail_falls_back(monkeypatch):
    d = _load(monkeypatch)

    class R(ctypes.Structure):
        _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                    ("r", ctypes.c_long), ("b", ctypes.c_long)]

    class U32:
        def GetWindowRect(self, hwnd, ptr):
            r = ctypes.cast(ptr, ctypes.POINTER(R)).contents
            r.l, r.t, r.r, r.b = 2, 12, 318, 228
            return True

    monkeypatch.setattr(ctypes, "windll",
                        types.SimpleNamespace(dwmapi=types.SimpleNamespace(
                            DwmGetWindowAttribute=lambda *a: 1),
                            user32=U32()))
    assert d.physical_window_bounds(7) == (2, 12, 318, 228)


def test_physical_bounds_gwr_fail_raises(monkeypatch):
    d = _load(monkeypatch)

    class U32:
        def GetWindowRect(self, hwnd, ptr):
            return False

    monkeypatch.setattr(ctypes, "windll",
                        types.SimpleNamespace(dwmapi=types.SimpleNamespace(
                            DwmGetWindowAttribute=lambda *a: 1),
                            user32=U32()))
    with pytest.raises(OSError):
        d.physical_window_bounds(7)


def test_physical_bounds_noop_off_windows(monkeypatch):
    d = _load(monkeypatch, plat="linux")
    with pytest.raises(OSError):
        d.physical_window_bounds(7)
