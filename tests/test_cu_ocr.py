"""cu_ocr.py unit tests — winrt/mss faked; runs on any platform."""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cu_load  # noqa: E402

cu_ocr = cu_load.load("cu_ocr")


class FakeImg:
    def __init__(self, w, h):
        self.width, self.height = w, h
        self.resized = None
        self.saved = []

    def resize(self, wh, resample=0):
        self.resized = wh
        out = FakeImg(*wh)
        return out

    def save(self, path, format=None):
        self.saved.append((path, format))


def test_upscale_skipped_when_tall(monkeypatch):
    img = FakeImg(400, 200)
    out, s = cu_ocr._upscaled(img)
    assert s == 1.0 and out is img


def test_upscale_small_image(monkeypatch):
    img = FakeImg(200, 20)
    out, s = cu_ocr._upscaled(img)
    assert s >= 4.0
    assert out.height >= cu_ocr._MIN_OCR_HEIGHT


def test_parse_region():
    assert cu_ocr._parse_region("1,2,300,400") == (1, 2, 300, 400)
    with pytest.raises(SystemExit):
        cu_ocr._parse_region("bogus")


def test_find_words_maps_to_screen(monkeypatch):
    monkeypatch.setattr(cu_ocr, "_grab_region",
                        lambda r: FakeImg(100, 100))
    monkeypatch.setattr(cu_ocr, "_ocr_words",
                        lambda p: [("Save", 10.0, 20.0, 40.0, 12.0),
                                   ("Cancel", 10.0, 40.0, 50.0, 12.0)])
    res = cu_ocr.find_words((500, 300, 100, 100), "save")
    matches, meta = res
    assert len(matches) == 1
    m = matches[0]
    assert m["text"] == "Save"
    assert m["x"] == 510.0 and m["y"] == 320.0
    assert m["cx"] == pytest.approx(530.0)
    assert meta["upscale"] == 1.0


def test_find_words_scaled_coordinates(monkeypatch):
    """Upscaled OCR boxes are divided back before offsetting."""
    small = FakeImg(100, 20)  # triggers upscale x4 (or more)
    monkeypatch.setattr(cu_ocr, "_grab_region", lambda r: small)

    def fake_resize(self, wh, resample=0):
        out = FakeImg(*wh)
        out.resized = wh
        return out
    monkeypatch.setattr(FakeImg, "resize", fake_resize)

    # word found at 40,80 in upscaled space (scale s) -> unscaled 40/s
    monkeypatch.setattr(cu_ocr, "_ocr_words",
                        lambda p: [("OK", 40.0, 80.0, 40.0, 40.0)])
    res = cu_ocr.find_words((10, 10, 100, 20), "ok")
    matches, meta = res
    s = meta["upscale"]
    assert s > 1.0
    assert matches[0]["x"] == round(40.0 / s + 10, 1)
    assert matches[0]["w"] == round(40.0 / s, 1)


def test_find_words_no_query_returns_all(monkeypatch):
    monkeypatch.setattr(cu_ocr, "_grab_region",
                        lambda r: FakeImg(100, 100))
    monkeypatch.setattr(cu_ocr, "_ocr_words",
                        lambda p: [("A", 0, 0, 5, 5), ("B", 1, 1, 5, 5)])
    matches, _ = cu_ocr.find_words((0, 0, 100, 100), None)
    assert len(matches) == 2


def test_find_words_grab_or_ocr_failure(monkeypatch):
    monkeypatch.setattr(cu_ocr, "_grab_region", lambda r: None)
    assert cu_ocr.find_words((0, 0, 100, 100), "x") is None
    monkeypatch.setattr(cu_ocr, "_grab_region",
                        lambda r: FakeImg(100, 100))
    monkeypatch.setattr(cu_ocr, "_ocr_words", lambda p: None)
    assert cu_ocr.find_words((0, 0, 100, 100), "x") is None


def test_find_words_empty_ocr(monkeypatch):
    monkeypatch.setattr(cu_ocr, "_grab_region",
                        lambda r: FakeImg(100, 100))
    monkeypatch.setattr(cu_ocr, "_ocr_words", lambda p: [])
    matches, _ = cu_ocr.find_words((0, 0, 100, 100), "x")
    assert matches == []


def test_ocr_words_returns_none_without_winrt(monkeypatch):
    """winrt absent in test env -> graceful None, not a crash."""
    monkeypatch.setitem(sys.modules, "winrt", None)
    for name in list(sys.modules):
        if name.startswith("winrt."):
            monkeypatch.setitem(sys.modules, name, None)
    assert cu_ocr._ocr_words("x.png") is None
