"""WT UIA read path — fake UIA provider objects behind the _io seam."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


class FakeTextPattern:
    def __init__(self, text):
        self._text = text

    def document_text(self):
        return self._text


class FakeTermControl:
    def __init__(self, text, focused=True):
        self._tp = FakeTextPattern(text)
        self.has_focus = focused

    def document_text(self):
        return self._tp.document_text()


TEXT = ("Microsoft Windows [Version 10]\n"
        "C:\\work>echo hello\n"
        "hello\n"
        "C:\\work>")


def _io(text=TEXT):
    return {"termcontrols": lambda hwnd: [FakeTermControl(text)],
            "class_name": lambda hwnd: "CASCADIA_HOSTING_WINDOW_CLASS"}


def test_read_wt_returns_full_text():
    out = t._read_wt(1, _io())
    assert out["ok"] is True
    assert "echo hello" in out["text"]
    assert "Microsoft Windows" in out["text"]


def test_read_tail():
    out = t._read_wt(1, _io(), tail=2)
    inner = [l for l in out["text"].splitlines()
             if "UNTRUSTED TERMINAL OUTPUT" not in l]
    assert inner == ["hello", "C:\\work>"]


def test_read_find():
    out = t._read_wt(1, _io(), find="hello")
    assert out["ok"] is True
    assert out["matches"] == 2


def test_read_wraps_untrusted():
    out = t._read_wt(1, _io())
    assert out["text"].startswith("--- BEGIN UNTRUSTED TERMINAL OUTPUT")
    assert out["text"].rstrip().endswith("---")


def test_read_no_termcontrol_errors():
    io = {"termcontrols": lambda hwnd: []}
    out = t._read_wt(1, io)
    assert out["ok"] is False


def test_multi_termcontrol_prefers_focused():
    io = {"termcontrols": lambda hwnd: [
        FakeTermControl("bg-tab", focused=False),
        FakeTermControl("fg-tab", focused=True)]}
    out = t._read_wt(1, io)
    assert "fg-tab" in out["text"]
