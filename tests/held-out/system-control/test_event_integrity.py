"""Held-out event-stream integrity contracts; lead-owned."""
import importlib
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


@pytest.fixture
def tel():
    try:
        return load("sc_telemetry")
    except ModuleNotFoundError:
        pytest.skip("sc_telemetry not implemented yet")


def ev(tel, pid, kind="process.exit", ts=None, attrs=None):
    return tel.normalize({"pid": pid, "start_time": 0}, source="t",
                         kind=kind, ts=ts, attrs=attrs)


def test_overflow_reports_dropped_and_bounds_drain(tel):
    s = tel.open_stream(capacity=4)["stream"]
    s.feed(ev(tel, i) for i in range(10))
    r = tel.drain(s.id, limit=100)
    assert len(r["value"]["events"]) <= 4
    assert r["evidence"]["dropped"] >= 6


def test_expired_cursor_returns_resync_not_skip(tel):
    s = tel.open_stream(capacity=4)["stream"]
    s.feed(ev(tel, i) for i in range(10))
    r = tel.drain(s.id, cursor=0, limit=100)
    assert r["value"]["resync_required"] is True


def test_secret_shaped_attrs_redacted(tel):
    e = ev(tel, 1, attrs={"password": "hunter2", "token": "t",
                          "note": "visible"})
    assert e["attrs"]["password"] != "hunter2"
    assert e["attrs"]["token"] != "t"
    assert e["attrs"]["note"] == "visible"


def test_clock_reversal_keeps_monotonic_cursor(tel):
    e1 = ev(tel, 1, ts=1000.0)
    e2 = ev(tel, 2, ts=500.0)
    assert e2["cursor"] > e1["cursor"]


def test_provider_failure_is_structured_not_raised(tel):
    def bad():
        raise RuntimeError("provider dead")

    s = tel.open_stream(capacity=8, provider=bad)["stream"]
    r = tel.drain(s.id, limit=10)
    assert isinstance(r, dict)
    assert r["ok"] is False


def test_closed_stream_rejects_drain(tel):
    s = tel.open_stream(capacity=4)["stream"]
    tel.close_stream(s.id)
    r = tel.drain(s.id, limit=10)
    assert r["ok"] is False
    assert r["status"] == "rejected"
