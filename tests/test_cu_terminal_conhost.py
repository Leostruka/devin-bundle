"""conhost read/write path — fake win32 console IO behind the _io seam."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


class FakeConOut:
    """Simulates AttachConsole + CONOUT$ + ReadConsoleOutputW."""

    def __init__(self, lines, cols=120, rows=9001, cursor=(40, 4)):
        self._lines = lines
        self.cols = cols
        self.rows = rows
        self.cursor = cursor
        self.attached = []
        self.written = []
        self.closed = False

    def attach(self, pid):
        self.attached.append(pid)
        return True

    def buffer_info(self):
        return {"cols": self.cols, "rows": self.rows,
                "cursor": list(self.cursor)}

    def read_lines(self):
        return list(self._lines)

    def write_input(self, text):
        self.written.append(text)
        return True

    def detach(self):
        self.closed = True


def _io(con):
    return {"conout": lambda pid: con,
            "class_name": lambda hwnd: "ConsoleWindowClass"}


LINES = ["D:\\work>echo conhost-ok", "conhost-ok", "", "D:\\work>"]


def test_read_conhost_full_buffer():
    con = FakeConOut(LINES)
    out = t._read_conhost(99, _io(con))
    assert out["ok"] is True
    assert "echo conhost-ok" in out["text"]
    assert con.attached == [99]
    assert con.closed is True  # FreeConsole always


def test_conhost_info():
    con = FakeConOut(LINES, cols=80, rows=50, cursor=(5, 10))
    out = t._conhost_info(99, _io(con))
    assert out["ok"] is True
    assert out["cols"] == 80
    assert out["rows"] == 50
    assert out["cursor"] == [5, 10]


def test_conhost_write_input():
    con = FakeConOut(LINES)
    out = t._conhost_send(99, "echo hi\r", _io(con))
    assert out["ok"] is True
    assert con.written == ["echo hi\r"]
    assert con.closed is True


def test_conhost_attach_fail():
    class BadCon(FakeConOut):
        def attach(self, pid):
            return False
    out = t._read_conhost(99, _io(BadCon(LINES)))
    assert out["ok"] is False
    assert "attach" in out["error"]
