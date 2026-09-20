"""backends.linux — fake-procfs seam tests (no real Linux required)."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
from backends import linux  # noqa: E402
from sc_backend import BackendUnavailable  # noqa: E402
from sc_contract import InvalidRequest  # noqa: E402

BTIME = 1_700_000_000
CLK = 100
TICKS = 200  # start_time = BTIME + TICKS/CLK = BTIME + 2


def _write_pid(root, pid, comm, ticks=TICKS):
    d = root / str(pid)
    d.mkdir(exist_ok=True)
    fields = ["S"] + ["0"] * 18 + [str(ticks)]
    (d / "stat").write_text(f"{pid} ({comm}) " + " ".join(fields))


@pytest.fixture
def fake_proc(tmp_path, monkeypatch):
    root = tmp_path / "proc"
    root.mkdir()
    (root / "stat").write_text(
        "cpu  0 0 0 0\nbtime %d\nprocesses 1\n" % BTIME)
    monkeypatch.setattr(linux, "PROC_ROOT", str(root))
    monkeypatch.setattr(linux, "_clock_ticks", lambda: CLK)
    return root


def test_process_get_roundtrip_identity(fake_proc):
    _write_pid(fake_proc, 42, "worker")
    p = linux.process_get(42, start_time=BTIME + TICKS // CLK)
    assert p == {"pid": 42, "start_time": BTIME + 2, "name": "worker"}


def test_process_get_comm_with_parens_and_spaces(fake_proc):
    _write_pid(fake_proc, 7, "weird (name) x")
    p = linux.process_get(7)
    assert p["name"] == "weird (name) x"
    assert p["start_time"] == BTIME + 2


def test_process_get_dead_pid_raises(fake_proc):
    with pytest.raises(LookupError):
        linux.process_get(999)


def test_process_get_stale_identity_raises(fake_proc):
    _write_pid(fake_proc, 42, "worker")
    with pytest.raises(LookupError, match="stale"):
        linux.process_get(42, start_time=BTIME + 999)


def test_process_list_scans_all_pids(fake_proc):
    for pid in (3, 9, 11):
        _write_pid(fake_proc, pid, f"p{pid}")
    procs = linux.process_list()
    assert [p["pid"] for p in procs] == [3, 9, 11]


def test_wait_process_rejects_stale_before_waiting(fake_proc):
    _write_pid(fake_proc, 42, "worker")
    r = linux.wait_process({"pid": 42, "start_time": BTIME + 999},
                           timeout_s=5)
    assert r["ok"] is False and r["status"] == "rejected"


def test_wait_process_rejects_dead_pid(fake_proc):
    r = linux.wait_process({"pid": 999, "start_time": 1}, timeout_s=5)
    assert r["ok"] is False and r["status"] == "rejected"


def test_wait_process_rejects_bad_timeout(fake_proc):
    _write_pid(fake_proc, 42, "worker")
    for bad in (-1, float("inf"), float("nan"), "x"):
        with pytest.raises(InvalidRequest):
            linux.wait_process({"pid": 42, "start_time": BTIME + 2},
                               timeout_s=bad)


def test_wait_process_prefers_pidfd(fake_proc, monkeypatch, tmp_path):
    _write_pid(fake_proc, 42, "worker")
    calls = []
    fd = os.open(tmp_path / "f", os.O_CREAT | os.O_RDWR)

    def fake_pidfd_open(pid, flags=0):
        calls.append(pid)
        return fd

    monkeypatch.setattr(os, "pidfd_open", fake_pidfd_open,
                        raising=False)
    r = linux.wait_process({"pid": 42, "start_time": BTIME + 2},
                           timeout_s=1)
    assert calls == [42]
    assert r["ok"] is True


def test_wait_process_poll_fallback_timeout(fake_proc, monkeypatch):
    _write_pid(fake_proc, 42, "worker")
    monkeypatch.delattr(os, "pidfd_open", raising=False)
    r = linux.wait_process({"pid": 42, "start_time": BTIME + 2},
                           timeout_s=0.3)
    assert r == {"ok": False, "status": "timeout"}


def test_wait_process_poll_detects_exit(fake_proc, monkeypatch):
    _write_pid(fake_proc, 42, "worker")
    monkeypatch.delattr(os, "pidfd_open", raising=False)
    real_get = linux.process_get
    state = {"calls": 0}

    def flaky_get(pid, start_time=None):
        state["calls"] += 1
        if state["calls"] == 1:
            return real_get(pid, start_time)
        raise LookupError(f"process not found: {pid}")

    monkeypatch.setattr(linux, "process_get", flaky_get)
    r = linux.wait_process({"pid": 42, "start_time": BTIME + 2},
                           timeout_s=5)
    assert r["ok"] is True and "exit_code" in r


def test_service_status_fixed_argv(fake_proc, monkeypatch):
    seen = []
    monkeypatch.setattr(linux, "_systemd", lambda: True)
    monkeypatch.setattr(
        linux, "run_bounded",
        lambda argv: (seen.append(list(argv)),
                      (0, b"active\n", b""))[1])
    r = linux.service_status("foo@bar.service")
    assert seen == [["systemctl", "show", "foo@bar.service",
                     "--property=ActiveState", "--value"]]
    assert r == {"name": "foo@bar.service", "state": "active"}


def test_service_status_requires_systemd(fake_proc, monkeypatch):
    monkeypatch.setattr(linux, "_systemd", lambda: False)
    with pytest.raises(BackendUnavailable):
        linux.service_status("sshd.service")


def test_service_status_rejects_bad_names(fake_proc):
    for bad in ("bad;name", "svc && rm", "", None):
        with pytest.raises(InvalidRequest):
            linux.service_status(bad)


def test_service_status_rc_nonzero_is_lookup(fake_proc, monkeypatch):
    monkeypatch.setattr(linux, "_systemd", lambda: True)
    monkeypatch.setattr(linux, "run_bounded",
                        lambda argv: (1, b"", b""))
    with pytest.raises(LookupError):
        linux.service_status("no-such.service")


def test_restart_service_never_direct(fake_proc):
    with pytest.raises(BackendUnavailable, match="broker"):
        linux.restart_service("sshd.service", allowed=["sshd.service"])


def test_capabilities_advertise_wait_and_restart(fake_proc):
    caps = {c["name"]: c for c in linux.capabilities()}
    wait = caps["process.wait"]
    assert wait["supported"] is True
    assert wait["mode"] == ("pidfd" if hasattr(os, "pidfd_open")
                            else "procfs-poll")
    restart = caps["service.restart"]
    assert restart["supported"] is False
    assert restart["reason"] == "broker_required"


def test_capabilities_wait_mode_pidfd(fake_proc, monkeypatch):
    monkeypatch.setattr(os, "pidfd_open", lambda pid: 0,
                        raising=False)
    caps = {c["name"]: c for c in linux.capabilities()}
    assert caps["process.wait"]["mode"] == "pidfd"
