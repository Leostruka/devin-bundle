"""cu_wgc.py unit tests — capability gating and error paths without
winrt/dxcam; the heavy path only runs on a host with deps installed."""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cu_load  # noqa: E402


def test_capability_false_off_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux", raising=False)
    mod = cu_load.load("cu_wgc")
    ok, why = mod.capability()
    assert ok is False and "windows" in why


def test_capability_false_without_deps(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32", raising=False)
    for name in list(sys.modules):
        if name.startswith(("winrt", "dxcam")):
            monkeypatch.setitem(sys.modules, name, None)
    mod = cu_load.load("cu_wgc")
    # force a fresh exec so the module-level sys.platform check reruns
    monkeypatch.delitem(sys.modules, "cu_wgc", raising=False)
    spec_mod = cu_load.load("cu_wgc")
    ok, why = spec_mod.capability()
    assert ok is False and "missing" in why


def test_shot_returns_error_not_crash(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32", raising=False)
    mod = cu_load.load("cu_wgc")
    monkeypatch.setattr(mod, "WgcWindow",
                        lambda h: (_ for _ in ()).throw(
                            RuntimeError("wgc deps missing")))
    img, err = mod.shot(123)
    assert img is None and "deps" in err


def test_drain_closes_each_frame(monkeypatch):
    mod = cu_load.load("cu_wgc")
    closed = []

    class F:
        def close(self):
            closed.append(1)

    class Pool:
        def __init__(self):
            self.frames = [F(), F(), None]

        def try_get_next_frame(self):
            return self.frames.pop(0)

    w = object.__new__(mod.WgcWindow)
    w.pool = Pool()
    assert w.drain() == 2 and len(closed) == 2


def test_next_frame_fresh_waits(monkeypatch):
    mod = cu_load.load("cu_wgc")
    w = object.__new__(mod.WgcWindow)

    class Ev:
        def __init__(self):
            self.waits = 0

        def clear(self):
            pass

        def wait(self, t):
            self.waits += 1
            return False  # timeout

    class Pool:
        def try_get_next_frame(self):
            return None

    w.pool, w._frame_ev = Pool(), Ev()
    w.drain = lambda: 0
    assert w.next_frame(0.01, fresh=True) is None
    assert w._frame_ev.waits == 1


def test_check_size_recreates_pool(monkeypatch):
    mod = cu_load.load("cu_wgc")
    w = object.__new__(mod.WgcWindow)
    w._psize = (100, 100)
    w._pixfmt = "P"
    w.winrt_dev = "D"
    calls = []

    class Pool:
        def recreate(self, dev, fmt, n, size):
            calls.append((int(size.width), int(size.height)))

    class Size:
        width, height = 200, 150

    frame = types.SimpleNamespace(content_size=Size())
    w.pool = Pool()
    w._check_size(frame)
    assert calls == [(200, 150)] and w._psize == (200, 150)


def test_cli_caps_json(monkeypatch, capsys):
    mod = cu_load.load("cu_wgc")
    monkeypatch.setattr(mod, "capability", lambda: (False, "no deps"))
    monkeypatch.setattr(sys, "argv", ["cu_wgc.py", "caps"])
    mod.main()
    out = capsys.readouterr().out
    import json
    d = json.loads(out)
    assert d["ok"] is True and d["available"] is False
