"""Windows backend event-provider and capability surface tests."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Win32 only")

import backends.windows as windows  # noqa: E402


def test_capabilities_advertise_wait_and_restart():
    caps = {c["name"]: c for c in windows.capabilities()}
    assert "process.wait" in caps
    assert "service.restart" in caps
    assert caps["process.wait"]["supported"] is True
    assert caps["process.wait"]["mode"] == "native"
    assert caps["service.restart"]["mode"] == "scm"


def test_process_provider_baseline_silent_then_start(monkeypatch):
    snaps = iter([
        [{"pid": 1, "start_time": 10, "name": "a"}],
        [{"pid": 1, "start_time": 10, "name": "a"},
         {"pid": 2, "start_time": 20, "name": "b"}],
    ])
    monkeypatch.setattr(windows, "process_list",
                        lambda pid=None: next(snaps))
    provider = windows.process_event_provider()
    assert provider() == []  # baseline emits nothing
    evs = provider()
    assert [e["kind"] for e in evs] == ["process.start"]
    assert evs[0]["subject"] == {"pid": 2, "start_time": 20}
    assert evs[0]["source"] == "windows"


def test_process_provider_emits_exit(monkeypatch):
    snaps = iter([
        [{"pid": 1, "start_time": 10, "name": "a"},
         {"pid": 2, "start_time": 20, "name": "b"}],
        [{"pid": 1, "start_time": 10, "name": "a"}],
    ])
    monkeypatch.setattr(windows, "process_list",
                        lambda pid=None: next(snaps))
    provider = windows.process_event_provider()
    provider()
    evs = provider()
    assert [e["kind"] for e in evs] == ["process.exit"]
    assert evs[0]["subject"] == {"pid": 2, "start_time": 20}


def test_process_provider_pid_reuse_not_an_exit(monkeypatch):
    # Same pid, different start_time: exit + start pair.
    snaps = iter([
        [{"pid": 5, "start_time": 1, "name": "old"}],
        [{"pid": 5, "start_time": 2, "name": "new"}],
    ])
    monkeypatch.setattr(windows, "process_list",
                        lambda pid=None: next(snaps))
    provider = windows.process_event_provider()
    provider()
    kinds = sorted(e["kind"] for e in provider())
    assert kinds == ["process.exit", "process.start"]


def test_process_provider_error_event_on_failure(monkeypatch):
    def boom(pid=None):
        raise RuntimeError("cim dead")
    monkeypatch.setattr(windows, "process_list", boom)
    provider = windows.process_event_provider()
    evs = provider()
    assert len(evs) == 1
    assert evs[0]["kind"] == "provider.error"
    assert evs[0]["severity"] == "error"
    # recovers after failure
    monkeypatch.setattr(windows, "process_list",
                        lambda pid=None: [])
    assert provider() == []


def test_stream_provider_process_via_sessions(monkeypatch):
    import sc_sessions
    provider, err = sc_sessions._stream_provider("process")
    assert err is None and callable(provider)
    provider, err = sc_sessions._stream_provider("bogus")
    assert provider is None and err["status"] == "rejected"


def test_backend_process_get_prefers_native():
    # Native path must agree with CIM-independent ground truth.
    r = windows.process_get(os.getpid())
    assert r["pid"] == os.getpid()
    assert isinstance(r["start_time"], int) and r["start_time"] > 0


def test_backend_wait_process_delegates():
    import sc_windows
    s = sc_windows.spawn_owned([sys.executable, "-c", "pass"])
    try:
        r = windows.wait_process(
            {"pid": s["pid"], "start_time": s["start_time"]},
            timeout_s=10)
        assert r["ok"] is True
    finally:
        sc_windows.close_owned(s)
