"""backends.macos — seam/monkeypatch tests (no real macOS required)."""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
from backends import macos  # noqa: E402
from sc_backend import BackendUnavailable  # noqa: E402
from sc_contract import InvalidRequest  # noqa: E402

PS_OUT = (
    b"  42 Mon Sep 19 12:00:00 2026 Ss   worker\n"
    b"   7 Mon Sep 19 12:00:00 2026 Ss   launchd\n"
    b"  99 Mon Sep 19 12:00:00 2026 Z    zombie\n"
)


@pytest.fixture
def fake_ps(monkeypatch):
    seen = []
    monkeypatch.setattr(macos.shutil, "which",
                        lambda c: f"/bin/{c}")
    monkeypatch.setattr(
        macos, "run_bounded",
        lambda argv: (seen.append(list(argv)), (0, PS_OUT, b""))[1])
    return seen


def _proc(pid=42, start_time=None):
    return {"pid": pid,
            "start_time": start_time if start_time is not None else 1,
            "name": "worker"}


def test_process_list_parses_lstart(fake_ps):
    procs = macos.process_list()
    assert [p["pid"] for p in procs] == [7, 42]
    assert all(isinstance(p["start_time"], int) for p in procs)
    assert fake_ps[0][:3] == ["ps", "-axo", "pid=,lstart=,stat=,comm="]
    assert 99 not in [p["pid"] for p in procs]  # zombies are dead


def test_process_get_stale_identity_raises(fake_ps):
    import time as _t
    started = int(_t.mktime(_t.strptime(
        "Mon Sep 19 12:00:00 2026", "%a %b %d %H:%M:%S %Y")))
    with pytest.raises(LookupError, match="stale"):
        macos.process_get(42, start_time=started + 1)


def test_service_status_label_gate_before_subprocess(monkeypatch):
    def boom(argv):
        raise AssertionError("run_bounded must not be called")

    monkeypatch.setattr(macos, "run_bounded", boom)
    for bad in ("", None, "bad;label", "svc && rm"):
        with pytest.raises(InvalidRequest):
            macos.service_status(bad)


def test_service_status_fixed_argv(fake_ps, monkeypatch):
    monkeypatch.setattr(macos.os, "getuid", lambda: 501,
                        raising=False)
    monkeypatch.setattr(
        macos, "run_bounded",
        lambda argv: (0, b"state = running\n", b""))
    r = macos.service_status("com.example.svc")
    assert r == {"name": "com.example.svc", "state": "running"}


def test_restart_service_never_direct():
    with pytest.raises(BackendUnavailable, match="broker"):
        macos.restart_service("com.example.svc",
                              allowed=["com.example.svc"])


def test_capabilities_honesty(monkeypatch):
    monkeypatch.setattr(macos.shutil, "which",
                        lambda c: f"/bin/{c}")
    caps = {c["name"]: c for c in macos.capabilities()}
    es = caps["endpoint_security"]
    assert es["supported"] is False
    assert es["reason"] == "entitlement_required"
    restart = caps["service.restart"]
    assert restart["supported"] is False
    assert restart["reason"] == "broker_required"
    wait = caps["process.wait"]
    assert wait["supported"] is True
    assert wait["mode"] == ("kqueue" if hasattr(macos.select, "kqueue")
                            else "ps-poll")


def test_wait_process_rejects_stale_identity(monkeypatch):
    monkeypatch.setattr(
        macos, "process_get",
        lambda pid, start_time=None: (
            (_ for _ in ()).throw(LookupError("stale pid identity"))))
    r = macos.wait_process({"pid": 42, "start_time": 1}, timeout_s=5)
    assert r["ok"] is False and r["status"] == "rejected"


def test_wait_process_rejects_dead_pid(monkeypatch):
    monkeypatch.setattr(
        macos, "process_get",
        lambda pid, start_time=None: (
            (_ for _ in ()).throw(LookupError("process not found"))))
    r = macos.wait_process({"pid": 42, "start_time": 1}, timeout_s=5)
    assert r["ok"] is False and r["status"] == "rejected"


def test_wait_process_rejects_bad_timeout(monkeypatch):
    monkeypatch.setattr(macos, "process_get",
                        lambda pid, start_time=None: _proc(pid))
    for bad in (-1, float("inf"), float("nan"), "x"):
        with pytest.raises(InvalidRequest):
            macos.wait_process({"pid": 42, "start_time": 1},
                               timeout_s=bad)


def test_wait_process_poll_detects_exit(monkeypatch):
    state = {"calls": 0}

    def flaky_get(pid, start_time=None):
        state["calls"] += 1
        if state["calls"] == 1:
            return _proc(pid)
        raise LookupError(f"process not found: {pid}")

    monkeypatch.setattr(macos, "process_get", flaky_get)
    r = macos.wait_process({"pid": 42, "start_time": 1}, timeout_s=5)
    assert r["ok"] is True


def test_wait_process_poll_timeout(monkeypatch):
    monkeypatch.setattr(macos, "process_get",
                        lambda pid, start_time=None: _proc(pid))
    r = macos.wait_process({"pid": 42, "start_time": 1},
                           timeout_s=0.3)
    assert r == {"ok": False, "status": "timeout"}


def _fake_kqueue_select(events):
    """Stub `select` module exposing a scripted kqueue."""
    class FakeKevent:
        def __init__(self, ident, filt, flags, fflags):
            self.ident = ident

    class FakeKqueue:
        closed = False
        registered = []

        def control(self, changelist, max_events, timeout=None):
            if changelist:
                self.registered.extend(changelist)
                return []
            return list(events)

        def close(self):
            self.closed = True

    return types.SimpleNamespace(
        kqueue=lambda: FakeKqueue(),
        kevent=FakeKevent,
        KQ_FILTER_PROC=-4,
        KQ_EV_ADD=1,
        KQ_EV_ERROR=0x4000,
        KQ_NOTE_EXIT=0x80000000)


def test_wait_process_kqueue_path(monkeypatch):
    event = object()
    fake_select = _fake_kqueue_select([event])
    monkeypatch.setattr(macos, "select", fake_select)
    monkeypatch.setattr(macos, "process_get",
                        lambda pid, start_time=None: _proc(pid))
    r = macos.wait_process({"pid": 42, "start_time": 1}, timeout_s=5)
    assert r["ok"] is True


def test_wait_process_kqueue_falls_back_to_recheck(monkeypatch):
    fake_select = _fake_kqueue_select([])
    monkeypatch.setattr(macos, "select", fake_select)
    state = {"calls": 0}

    def flaky_get(pid, start_time=None):
        state["calls"] += 1
        if state["calls"] == 1:
            return _proc(pid)
        raise LookupError(f"process not found: {pid}")

    monkeypatch.setattr(macos, "process_get", flaky_get)
    r = macos.wait_process({"pid": 42, "start_time": 1}, timeout_s=5)
    assert r["ok"] is True


def test_wait_process_identity_must_be_object():
    with pytest.raises(InvalidRequest):
        macos.wait_process(42, timeout_s=1)
