"""Gate for ticket 04: authorized-browser binding contract. All state via
injected paths/pids — no real browser, no network."""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
br = cu_load.load("cu_browser")


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "_BINDING_OVERRIDE", str(tmp_path / "bind.json"))
    monkeypatch.setattr(cu_load.sys.modules["cu_hints"], "session_id",
                        lambda: "sess-test")
    yield


def test_bind_writes_binding():
    r = br.bind("http://127.0.0.1:9222", 4321)
    assert r["ok"] is True
    b = br.binding()
    assert b["endpoint"] == "http://127.0.0.1:9222"
    assert b["pid"] == 4321
    assert b["session_id"] == "sess-test"


def test_bind_rejects_non_loopback():
    for ep in ("http://192.168.1.5:9222", "http://0.0.0.0:9222",
               "http://example.com:9222", "ws://127.0.0.1:9222", ""):
        assert br.bind(ep, 1234)["ok"] is False, ep
    assert br.binding() is None


def test_bind_rejects_bad_pid():
    assert br.bind("http://127.0.0.1:9222", 0)["ok"] is False
    assert br.bind("http://127.0.0.1:9222", -3)["ok"] is False
    assert br.bind("http://127.0.0.1:9222", "1234")["ok"] is False


def test_unbound_check_rejects():
    assert br.check(999) == (False, "no_binding")


def test_check_foreign_process_rejects(monkeypatch):
    br.bind("http://127.0.0.1:9222", 4321)
    monkeypatch.setattr(br, "_hwnd_pid", lambda hwnd: 7777)
    assert br.check(999) == (False, "foreign_process")


def test_check_bound_process_allows(monkeypatch):
    br.bind("http://127.0.0.1:9222", 4321)
    monkeypatch.setattr(br, "_hwnd_pid", lambda hwnd: 4321)
    assert br.check(999) == (True, None)


def test_check_unknown_owner_rejects(monkeypatch):
    br.bind("http://127.0.0.1:9222", 4321)
    monkeypatch.setattr(br, "_hwnd_pid", lambda hwnd: 0)
    assert br.check(999) == (False, "unknown_owner")


def test_binding_expires(monkeypatch):
    br.bind("http://127.0.0.1:9222", 4321)
    # age the file beyond TTL
    p = br._path()
    d = json.load(open(p, encoding="utf-8"))
    d["created_at"] = time.time() - br.BINDING_TTL_S - 1
    json.dump(d, open(p, "w", encoding="utf-8"))
    assert br.binding() is None
    assert br.check(1)[0] is False


def test_binding_rejects_other_session(monkeypatch):
    br.bind("http://127.0.0.1:9222", 4321)
    hints = cu_load.sys.modules["cu_hints"]
    monkeypatch.setattr(hints, "session_id", lambda: "sess-OTHER")
    assert br.binding() is None


def test_unbind_removes():
    br.bind("http://127.0.0.1:9222", 4321)
    assert br.unbind()["ok"] is True
    assert br.binding() is None


def test_cdp_client_honest_unavailable():
    """No approved driver installed -> None, never a silent stub."""
    assert br._cdp_client() is None


def test_viewport_to_desktop_conversion():
    """CSS px and desktop px are distinct spaces; conversion is explicit."""
    # dpr 2 display, viewport at desktop (300, 200)
    assert br.viewport_to_desktop(10, 20, (300, 200), dpr=2.0) == (320, 240)
    # dpr 1: pure translation
    assert br.viewport_to_desktop(10, 20, (300, 200), dpr=1.0) == (310, 220)
    # negative-origin monitor
    assert br.viewport_to_desktop(0, 0, (-1920, 0), dpr=1.0) == (-1920, 0)
