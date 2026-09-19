"""Terminal binding contract — same session+TTL rules as cu_browser.
All window/console state via injected seams — no real terminal."""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "_BINDING_OVERRIDE", str(tmp_path / "tbind.json"))
    monkeypatch.setattr(cu_load.sys.modules["cu_hints"], "session_id",
                        lambda: "sess-test")
    yield


def _probe(hwnd, cls, pid):
    return {hwnd: {"class": cls, "pid": pid}}


def test_bind_writes_binding():
    r = t.bind(hwnd=10, probe=_probe(10, "CASCADIA_HOSTING_WINDOW_CLASS", 111))
    assert r["ok"] is True
    b = t.binding()
    assert b["hwnd"] == 10
    assert b["pid"] == 111
    assert b["mode"] == "wt"
    assert b["session_id"] == "sess-test"


def test_bind_conhost_mode():
    r = t.bind(hwnd=20, probe=_probe(20, "ConsoleWindowClass", 222))
    assert r["ok"] is True
    assert t.binding()["mode"] == "conhost"


def test_bind_mintty_mode():
    r = t.bind(hwnd=30, probe=_probe(30, "mintty", 333))
    assert r["ok"] is True
    assert t.binding()["mode"] == "mintty"


def test_bind_rejects_unknown_class():
    r = t.bind(hwnd=40, probe=_probe(40, "Chrome_WidgetWin_1", 444))
    assert r["ok"] is False
    assert "class" in r["error"] or "unknown" in r["error"]
    assert t.binding() is None


def test_bind_rejects_bad_hwnd():
    assert t.bind(hwnd=0, probe={})["ok"] is False
    assert t.bind(hwnd=-5, probe={})["ok"] is False
    assert t.bind(hwnd="abc", probe={})["ok"] is False


def test_unbind_clears():
    t.bind(hwnd=10, probe=_probe(10, "mintty", 1))
    assert t.binding() is not None
    assert t.unbind()["ok"] is True
    assert t.binding() is None


def test_binding_rejects_other_session():
    t.bind(hwnd=10, probe=_probe(10, "mintty", 1))
    path = t._BINDING_OVERRIDE
    data = json.loads(open(path).read())
    data["session_id"] = "other-sess"
    open(path, "w").write(json.dumps(data))
    assert t.binding() is None


def test_binding_rejects_expired(monkeypatch):
    t.bind(hwnd=10, probe=_probe(10, "mintty", 1))
    real = time.time
    monkeypatch.setattr(time, "time", lambda: real() + 99999)
    assert t.binding() is None


def test_check_requires_binding():
    assert t.check() == (False, "no_binding")


def test_check_ok_when_bound():
    t.bind(hwnd=10, probe=_probe(10, "mintty", 1))
    assert t.check() == (True, None)
