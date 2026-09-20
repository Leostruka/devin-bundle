"""Event streams: backend providers, daemon hosting, CLI surface."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_cli  # noqa: E402
import sc_sessions  # noqa: E402
import sc_telemetry as telemetry  # noqa: E402


class FakeBackend:
    name = "fake"
    procs = []
    def capabilities(self):
        return [{"name": "process.observe", "supported": True,
                 "reason": None, "mode": "native"},
                {"name": "events.process", "supported": True,
                 "reason": None, "mode": "poll"}]
    def process_list(self, pid=None):
        return list(self.procs)
    def process_event_provider(self):
        from backends import make_process_provider
        return make_process_provider(lambda: self.process_list(),
                                     self.name)


def test_process_provider_baseline_then_diff():
    fb = FakeBackend()
    fb.procs = [{"pid": 1, "start_time": 10, "name": "a"}]
    prov = fb.process_event_provider()
    assert prov() == []  # baseline emits nothing
    fb.procs.append({"pid": 2, "start_time": 20, "name": "b"})
    evs = prov()
    assert [e["kind"] for e in evs] == ["process.start"]
    assert evs[0]["subject"] == {"pid": 2, "start_time": 20}
    assert evs[0]["attrs"]["name"] == "b"
    fb.procs = [{"pid": 2, "start_time": 20, "name": "b"}]
    evs = prov()
    assert [e["kind"] for e in evs] == ["process.exit"]
    assert evs[0]["subject"] == {"pid": 1, "start_time": 10}


def test_process_provider_snapshot_failure_is_event():
    def bad():
        raise RuntimeError("snap")
    from backends import make_process_provider
    prov = make_process_provider(bad, "fake")
    evs = prov()
    assert len(evs) == 1
    assert evs[0]["kind"] == "provider.error"
    assert evs[0]["severity"] == "error"


@pytest.fixture
def daemon(tmp_path, monkeypatch):
    pf = str(tmp_path / "pidfile.json")
    monkeypatch.setattr(sc_sessions, "PIDFILE", pf)
    monkeypatch.setattr(sc_sessions, "IDLE_TTL_S", 120)
    yield pf
    sc_sessions.stop_daemon()


def test_daemon_stream_roundtrip(daemon):
    assert sc_sessions.start_daemon()["ok"]
    r = telemetry.open_stream_remote(capacity=16, ttl_s=60)
    assert r["ok"] is True
    sid = r["stream"]["id"]
    listed = telemetry.list_streams_remote()
    assert listed["ok"] and any(s["id"] == sid
                              for s in listed["streams"])
    d = telemetry.drain_remote(sid)
    assert d["ok"] and d["status"] == "verified"
    assert d["value"]["events"] == []
    c = telemetry.close_stream_remote(sid)
    assert c["ok"] is True
    d2 = telemetry.drain_remote(sid)
    assert d2["ok"] is False and d2["status"] == "rejected"


def test_daemon_stream_unknown_provider_rejected(daemon):
    assert sc_sessions.start_daemon()["ok"]
    r = telemetry.open_stream_remote(provider="bogus")
    assert r["ok"] is False and r["status"] == "rejected"


def test_daemon_stream_process_provider_polls(daemon):
    assert sc_sessions.start_daemon()["ok"]
    r = telemetry.open_stream_remote(provider="process",
                                     interval_s=1.0, ttl_s=60)
    assert r["ok"], r
    sid = r["stream"]["id"]
    d = telemetry.drain_remote(sid)
    assert d["ok"] and d["status"] == "verified"
    assert isinstance(d["value"]["events"], list)
    telemetry.close_stream_remote(sid)


def _run(argv, capsys):
    code = sc_cli.main(argv)
    out = capsys.readouterr().out.strip()
    return code, json.loads(out)


def test_cli_events_drain_requires_stream_id(capsys):
    code, r = _run(["events", "drain"], capsys)
    assert code == 2 and r["ok"] is False and r["status"] == "rejected"


def test_cli_events_unknown_subcommand(capsys):
    code, r = _run(["events", "bogus"], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_events_unknown_flag(capsys):
    code, r = _run(["events", "open", "--wat", "1"], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_events_no_daemon(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_sessions, "PIDFILE",
                        str(tmp_path / "none.json"))
    monkeypatch.setattr(sc_sessions, "start_daemon",
                        lambda: {"ok": False,
                                 "error": "daemon unavailable"})
    code, r = _run(["events", "drain", "--stream-id", "abc"], capsys)
    assert code in (1, 2) and r["ok"] is False


def test_daemon_stream_drain_rejects_nonstring_id(daemon):
    assert sc_sessions.start_daemon()["ok"]
    r = telemetry.drain_remote(["not", "a", "string"])
    assert r["ok"] is False and r["status"] == "rejected"
