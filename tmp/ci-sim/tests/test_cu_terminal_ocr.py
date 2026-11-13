"""mintty OCR read — winrt seam: text when engine present, pixels fallback."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "_BINDING_OVERRIDE", str(tmp_path / "b.json"))
    monkeypatch.setattr(cu_load.sys.modules["cu_hints"], "session_id",
                        lambda: "sess-test")
    monkeypatch.setattr(t, "_window_rect", lambda hwnd: (0, 0, 800, 600))
    yield


def _probe(hwnd, cls, pid):
    return {hwnd: {"class": cls, "pid": pid, "title": "MINGW64:~"}}


def _io(ocr=None, shot="/tmp/shot.png"):
    return {"screenshot_region": lambda rect: shot,
            "ocr": (lambda p: ocr)}


def test_mintty_read_ocr_text():
    t.bind(hwnd=30, probe=_probe(30, "mintty", 333))
    r = t.read(io=_io(ocr="user@host MINGW64 ~\n$ echo hi\nhi"))
    assert r["ok"] is True and r["mode"] == "mintty"
    assert r["ocr"] is True
    assert "echo hi" in r["text"]
    assert "UNTRUSTED" in r["text"]
    assert r["image"] == "/tmp/shot.png"


def test_mintty_read_no_ocr_falls_back():
    t.bind(hwnd=30, probe=_probe(30, "mintty", 333))
    r = t.read(io=_io(ocr=None))
    assert r["ok"] is True
    assert r["ocr"] is False
    assert "text" not in r
    assert r["image"] == "/tmp/shot.png"


def test_ocr_image_no_winrt(monkeypatch):
    # winrt absent → None, not an exception
    monkeypatch.setitem(sys.modules, "winrt", None)
    monkeypatch.setitem(sys.modules, "winrt.windows", None)
    monkeypatch.setitem(sys.modules,
                        "winrt.windows.media.ocr", None)
    assert t._ocr_image("/nope.png") is None
