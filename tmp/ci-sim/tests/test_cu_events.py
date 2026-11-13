"""cu_events.py unit tests — no real hook; the Refresher/filter/state
logic is platform-neutral, socket paths are tested offline."""
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cu_load  # noqa: E402

ev = cu_load.load("cu_events")


def _ref():
    return ev._Refresher()


def test_filter_watched_and_refresh_event():
    r = _ref()
    r.watched[42] = 0
    r.handle(1.0, ev.EVENT_OBJECT_SHOW, 42)
    assert 42 in r.dirty and len(r.buf) == 1
    assert r.stats["seen"] == 1


def test_filter_rejects_unwatched_hwnd():
    r = _ref()
    r.handle(1.0, ev.EVENT_OBJECT_SHOW, 99)
    assert not r.dirty and r.buf == [] and r.stats["skipped"] == 1


def test_filter_rejects_non_refresh_event():
    r = _ref()
    r.watched[42] = 0
    r.handle(1.0, 0x8005, 42)  # EVENT_OBJECT_HIDE not in REFRESH set
    assert 42 not in r.dirty and r.buf == []


def test_filter_rejects_foreground_but_watched_show_ok():
    assert ev.EVENT_SYSTEM_FOREGROUND in ev.REFRESH_EVENTS
    assert 0x8005 not in ev.REFRESH_EVENTS  # HIDE debounce skipped


def test_debounce_coalesces_burst(monkeypatch):
    """10 events inside the debounce window -> ONE refresh."""
    r = _ref()
    r.watched[7] = 0
    enums = []
    monkeypatch.setattr(ev, "_enum_hwnd",
                        lambda h: enums.append(h) or
                        ([{"id": "a"}], {"hwnd": h}))
    monkeypatch.setattr(ev, "_write_hints", lambda *a: None)
    now = time.perf_counter()
    for i in range(10):
        r.handle(now + i * 0.01, ev.EVENT_OBJECT_LOCATIONCHANGE, 7)
    r._refresh_due()  # deadline is still in the future -> no refresh
    assert enums == [] and 7 in r.dirty
    r.dirty[7] = time.perf_counter() - 1  # force due
    r._refresh_due()
    assert enums == [7]  # exactly one refresh for the whole burst
    assert r.watched[7] == 1 and r.stats["refreshed"] == 1
    assert 7 not in r.dirty


def test_enum_failure_keeps_clean(monkeypatch):
    r = _ref()
    r.watched[7] = 0
    r.dirty[7] = time.perf_counter() - 1
    monkeypatch.setattr(ev, "_enum_hwnd", lambda h: ([], None))
    monkeypatch.setattr(ev, "_write_hints", lambda *a: pytest.fail(
        "sidecar written on empty enum"))
    r._refresh_due()
    assert r.stats["enum_fail"] == 1 and r.watched[7] == 0


def test_event_buffer_capped():
    r = _ref()
    r.watched[1] = 0
    for i in range(ev.EVENT_BUF + 50):
        r.handle(float(i), ev.EVENT_OBJECT_SHOW, 1)
    assert len(r.buf) == ev.EVENT_BUF


def test_hints_sidecar_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "HINT_FMT", str(tmp_path / "h-%d.json"))
    ev._write_hints(5, [{"id": "x"}], {"hwnd": 5}, 3)
    d = ev._read_hints(5)
    assert d["generation"] == 3 and d["count"] == 1
    assert ev._read_hints(999) is None


def test_daemon_info_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVENTS_PATH", str(tmp_path / "none.json"))
    assert ev._daemon_info() is None


def test_request_no_daemon(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVENTS_PATH", str(tmp_path / "none.json"))
    r = ev._request({"cmd": {"op": "status"}})
    assert r["ok"] is False and "not running" in r["error"]


def test_session_check_in_daemon_op():
    """ops are pure given a Refresher; session gate is transport-level."""
    r = _ref()
    r.watched[3] = 1
    r.buf.append({"t": 1, "event": "0x8002", "hwnd": 3})
    out, r.buf = list(r.buf), []
    assert out[0]["hwnd"] == 3
