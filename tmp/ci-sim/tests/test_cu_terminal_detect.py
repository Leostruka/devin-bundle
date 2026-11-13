"""Terminal surface classification — pure logic over injected probes."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


@pytest.mark.parametrize("cls,expected", [
    ("CASCADIA_HOSTING_WINDOW_CLASS", "wt"),
    ("ConsoleWindowClass", "conhost"),
    ("mintty", "mintty"),
    ("mintty_2", "mintty"),
    ("Chrome_WidgetWin_1", "unknown"),
    ("", "unknown"),
    (None, "unknown"),
])
def test_classify(cls, expected):
    assert t.classify(cls) == expected


def test_detect_returns_mode_and_owner():
    probe = {77: {"class": "ConsoleWindowClass", "pid": 900,
                 "title": "cmd"}}
    d = t.detect(77, probe=probe)
    assert d["mode"] == "conhost"
    assert d["hwnd"] == 77
    assert d["pid"] == 900


def test_detect_unknown_hwnd():
    d = t.detect(999, probe={})
    assert d["mode"] == "unknown"
    assert d["hwnd"] == 999
