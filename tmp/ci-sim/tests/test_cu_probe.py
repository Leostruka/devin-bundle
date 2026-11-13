"""cu_probe.py unit tests — edge-scan geometry on synthetic buffers and
typed failure paths; no screen, UIA, or capture hardware required."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cu_load  # noqa: E402


class FakeImg:
    def __init__(self, w, h, rgb):
        self.width, self.height, self.rgb = w, h, rgb
        self.size = (w, h)


def make_img(w, h, fill=(10, 10, 10), box=None, box_color=(200, 200, 200)):
    """RGB buffer with an optional filled rect box=(l,t,r,b) inclusive."""
    buf = bytearray(fill * (w * h))
    if box:
        l, t, r, b = box
        for y in range(t, b + 1):
            for x in range(l, r + 1):
                i = (y * w + x) * 3
                buf[i:i + 3] = bytes(box_color)
    return FakeImg(w, h, bytes(buf))


def test_edge_box_finds_rect():
    mod = cu_load.load("cu_probe")
    img = make_img(40, 30, box=(10, 8, 29, 21))
    l, t, r, b, hit = mod._edge_box(img, 20, 15, tolerance=30)
    assert (l, t, r, b) == (10, 8, 29, 21)
    assert hit is False


def test_edge_box_seed_on_background_covers_image():
    mod = cu_load.load("cu_probe")
    img = make_img(40, 30, box=(10, 8, 29, 21))
    # seed on background color -> region = whole image (minus the box
    # column/row interruptions do NOT stop the scan: scans run along the
    # seed row/col only, so a seed outside the box's span reaches edges)
    l, t, r, b, hit = mod._edge_box(img, 35, 25, tolerance=30)
    assert (l, t, r, b) == (0, 0, 39, 29)
    assert hit is True


def test_edge_box_tolerance_zero_is_strict():
    mod = cu_load.load("cu_probe")
    img = make_img(10, 10)
    # single different pixel at (5,5)
    buf = bytearray(img.rgb)
    i = (5 * 10 + 5) * 3
    buf[i:i + 3] = b"\x20\x20\x20"
    img = FakeImg(10, 10, bytes(buf))
    l, t, r, b, hit = mod._edge_box(img, 5, 5, tolerance=0)
    assert (l, t, r, b) == (5, 5, 5, 5)
    assert hit is False


def test_monitor_for_picks_containing():
    mod = cu_load.load("cu_probe")
    mons = [{"left": 0, "top": 0, "width": 3000, "height": 1080},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
            {"left": 1920, "top": 0, "width": 1080, "height": 1080}]
    assert mod._monitor_for(100, 50, mons)["width"] == 1920
    assert mod._monitor_for(2000, 50, mons)["left"] == 1920
    # point off all real monitors -> virtual union fallback
    assert mod._monitor_for(-500, -500, mons) is mons[0]


def test_probe_edges_maps_to_screen_coords(monkeypatch):
    mod = cu_load.load("cu_probe")
    img = make_img(40, 30, box=(10, 8, 29, 21))
    fake_cap = type(sys)("cu_capture")
    fake_cap.monitors = lambda: [
        {"left": 0, "top": 0, "width": 40, "height": 30},
        {"left": 0, "top": 0, "width": 40, "height": 30}]
    fake_cap.grab = lambda bbox: (img, {})
    monkeypatch.setitem(sys.modules, "cu_capture", fake_cap)
    res, err = mod.probe_edges(20, 15)
    assert err is None
    assert res["bounds"] == [10, 8, 20, 14]
    assert res["hit_image_edge"] is False


def test_probe_edges_outside_capture(monkeypatch):
    mod = cu_load.load("cu_probe")
    img = make_img(40, 30)
    fake_cap = type(sys)("cu_capture")
    fake_cap.monitors = lambda: [
        {"left": 0, "top": 0, "width": 40, "height": 30},
        {"left": 0, "top": 0, "width": 40, "height": 30}]
    fake_cap.grab = lambda bbox: (img, {})
    monkeypatch.setitem(sys.modules, "cu_capture", fake_cap)
    # virtual-union fallback puts the point back in-range only if inside
    res, err = mod.probe_edges(999, 999)
    # _monitor_for falls back to mons[0] (0,0,40,30) -> point outside
    assert res is None and err == "point_outside_capture"


def test_probe_uia_off_platform(monkeypatch):
    mod = cu_load.load("cu_probe")
    monkeypatch.setattr(sys, "platform", "linux", raising=False)
    res, err = mod.probe_uia(10, 10)
    assert res is None and err == "no_uia"
