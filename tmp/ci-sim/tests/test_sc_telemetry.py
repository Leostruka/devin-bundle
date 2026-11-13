"""sc_telemetry — normalized envelopes, bounded streams, reducer."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_telemetry as telemetry  # noqa: E402


def test_normalize_shape():
    e = telemetry.normalize({"pid": 7, "start_time": 9},
                            source="fake", kind="process.exit")
    assert e["subject"] == {"pid": 7, "start_time": 9}
    assert e["source"] == "fake" and e["kind"] == "process.exit"
    assert e["severity"] == "info"
    assert isinstance(e["ts"], float) and isinstance(e["observed_ts"], float)
    assert isinstance(e["cursor"], int) and e["dropped"] == 0


def test_normalize_cursor_monotonic_despite_reversed_ts():
    a = telemetry.normalize({}, source="s", kind="k", ts=time.time())
    b = telemetry.normalize({}, source="s", kind="k", ts=1.0)
    assert b["cursor"] > a["cursor"]


def test_normalize_redacts_secret_keys():
    e = telemetry.normalize({}, source="s", kind="k", attrs={
        "password": "x", "API_KEY": "y", "authToken": "z",
        "Set-Cookie": "c", "private-key": "p", "name": "ok"})
    assert e["attrs"]["password"] == "***"
    assert e["attrs"]["API_KEY"] == "***"
    assert e["attrs"]["authToken"] == "***"
    assert e["attrs"]["Set-Cookie"] == "***"
    assert e["attrs"]["private-key"] == "***"
    assert e["attrs"]["name"] == "ok"


def test_normalize_nested_attr_redacted():
    e = telemetry.normalize({}, source="s", kind="k", attrs={
        "cfg": {"password": "x"}, "items": [1, "secret"], "n": 3})
    assert e["attrs"]["cfg"] == "***"
    assert e["attrs"]["items"] == "***"
    assert "x" not in str(e["attrs"])
    assert e["attrs"]["n"] == "3"


def test_open_stream_rejects_nonfinite_and_bool():
    for bad in (float("nan"), float("inf"), True, "x"):
        assert telemetry.open_stream(ttl_s=bad)["status"] == "rejected"
        assert telemetry.open_stream(capacity=bad)["status"] == \
            "rejected"
        assert telemetry.open_stream(interval_s=bad)["status"] == \
            "rejected"


def test_feed_skips_non_dict_items():
    s = telemetry.open_stream(capacity=8)["stream"]
    s.feed([telemetry.normalize({}, source="t", kind="k"),
            "junk", 42, None])
    r = telemetry.drain(s.id)
    assert len(r["value"]["events"]) == 1
    telemetry.close_stream(s.id)


def test_provider_dict_return_yields_error_event():
    s = telemetry.open_stream(capacity=8,
                              provider=lambda: {"a": 1})["stream"]
    r = telemetry.drain(s.id)
    assert r["ok"] is True
    assert len(r["value"]["events"]) == 1
    assert r["value"]["events"][0]["kind"] == "provider.error"
    telemetry.close_stream(s.id)


def test_hosted_stream_drain_does_not_poll_inline():
    calls = {"n": 0}
    def prov():
        calls["n"] += 1
        return [telemetry.normalize({}, source="p", kind="tick")]
    s = telemetry.open_stream(capacity=8, provider=prov)["stream"]
    s.hosted = True  # daemon-owned: poller thread feeds it
    r = telemetry.drain(s.id)
    assert r["ok"] and calls["n"] == 0
    s.feed([telemetry.normalize({}, source="p", kind="tick")])
    r2 = telemetry.drain(s.id)
    assert len(r2["value"]["events"]) == 1 and calls["n"] == 0
    telemetry.close_stream(s.id)


def test_normalize_attr_caps():
    attrs = {f"k{i}": "v" for i in range(40)}
    e = telemetry.normalize({}, source="s", kind="k", attrs=attrs)
    assert len(e["attrs"]) == 32
    e2 = telemetry.normalize({}, source="s", kind="k",
                             attrs={"big": "x" * 600})
    assert len(e2["attrs"]["big"]) < 600
    assert e2["attrs"]["big"].endswith("]")
    e3 = telemetry.normalize({}, source="s", kind="k", attrs="junk")
    assert e3["attrs"] == {}


def test_open_feed_drain_roundtrip():
    r = telemetry.open_stream(capacity=16)
    assert r["ok"] is True
    s = r["stream"]
    assert s.id
    evs = [telemetry.normalize({"pid": i, "start_time": 1},
                               source="t", kind="k") for i in range(5)]
    s.feed(evs)
    d = telemetry.drain(s.id)
    assert d["ok"] and d["status"] == "verified"
    assert len(d["value"]["events"]) == 5
    assert d["value"]["cursor"] == evs[-1]["cursor"]
    assert d["value"]["resync_required"] is False
    assert d["evidence"]["dropped"] == 0


def test_drain_bounded_and_reports_drops():
    s = telemetry.open_stream(capacity=8)["stream"]
    s.feed(telemetry.normalize({}, source="t", kind="k")
           for _ in range(20))
    r = telemetry.drain(s.id, limit=5)
    assert len(r["value"]["events"]) == 5
    assert r["evidence"]["dropped"] == 12


def test_drain_cursor_resume_and_resync():
    s = telemetry.open_stream(capacity=4)["stream"]
    evs = [telemetry.normalize({}, source="t", kind="k")
           for _ in range(6)]
    s.feed(evs)
    r = telemetry.drain(s.id, cursor=evs[0]["cursor"])
    assert r["value"]["resync_required"] is True
    assert [e["cursor"] for e in r["value"]["events"]] == \
        [e["cursor"] for e in evs[-4:]]
    r2 = telemetry.drain(s.id, cursor=evs[3]["cursor"])
    assert r2["value"]["resync_required"] is False
    assert [e["cursor"] for e in r2["value"]["events"]] == \
        [e["cursor"] for e in evs[4:]]


def test_drain_unknown_and_closed_rejected():
    assert telemetry.drain("nope")["ok"] is False
    assert telemetry.drain("nope")["status"] == "rejected"
    s = telemetry.open_stream(capacity=4)["stream"]
    assert telemetry.close_stream(s.id)["ok"] is True
    r = telemetry.drain(s.id)
    assert r["ok"] is False and r["status"] == "rejected"


def test_drain_provider_exception_structured():
    def bad():
        raise RuntimeError("boom")
    s = telemetry.open_stream(capacity=4, provider=bad)["stream"]
    r = telemetry.drain(s.id)
    assert r["ok"] is False and r["status"] == "unknown"
    telemetry.close_stream(s.id)


def test_drain_provider_feeds_events():
    calls = {"n": 0}
    def prov():
        calls["n"] += 1
        return [telemetry.normalize({"n": calls["n"]},
                                    source="p", kind="tick")]
    s = telemetry.open_stream(capacity=4, provider=prov)["stream"]
    r = telemetry.drain(s.id)
    assert r["ok"] and len(r["value"]["events"]) == 1
    telemetry.close_stream(s.id)


def test_stream_ttl_expiry_rejects():
    s = telemetry.open_stream(capacity=4, ttl_s=60)["stream"]
    s.created_at -= 120
    r = telemetry.drain(s.id)
    assert r["ok"] is False and r["status"] == "rejected"
    telemetry.close_stream(s.id)


def test_reduce_events_groups_and_keeps_errors():
    ev = lambda kind, pid, sev="info", dropped=0: dict(
        telemetry.normalize({"pid": pid}, source="t", kind=kind,
                            severity=sev), dropped=dropped)
    r = telemetry.reduce_events(
        [ev("a", 1), ev("a", 1), ev("b", 2, sev="error"),
         ev("buffer.overflow", 3, dropped=4)], top_k=1)
    assert r["total"] == 4 and r["dropped"] == 4
    assert len(r["groups"]) == 1 and r["groups"][0]["count"] == 2
    assert len(r["errors"]) == 2
    assert r["errors"][0]["subject"]["pid"] == 2
