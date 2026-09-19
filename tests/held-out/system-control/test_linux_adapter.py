"""Held-out Linux adapter contracts; lead-owned.

Seam-based: runs on any host via an injected fake procfs root.
Boot time is 1000s, clock ticks 100/s (impl defaults when sysconf
unavailable).
"""
import importlib
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


@pytest.fixture
def linux(tmp_path, monkeypatch):
    lx = load("backends.linux")
    (tmp_path / "stat").write_text("btime 1000\n")
    monkeypatch.setattr(lx, "PROC_ROOT", str(tmp_path))
    return lx


def fake_proc(root, pid, name="proc", start_ticks=100, state="S"):
    d = Path(root) / str(pid)
    d.mkdir()
    (d / "stat").write_text(f"{pid} ({name}) {state} " + "0 " * 19 +
                            str(start_ticks))
    (d / "comm").write_text(name + "\n")
    return d


def test_procfs_identity_uses_stable_start(linux, tmp_path):
    fake_proc(tmp_path, 4242, name="myp", start_ticks=200)
    r = linux.process_get(4242)
    assert r["pid"] == 4242
    assert r["start_time"] > 0
    # roundtrip: identity must verify against itself
    r2 = linux.process_get(4242, start_time=r["start_time"])
    assert r2["pid"] == 4242


def test_stale_start_time_rejected(linux, tmp_path):
    fake_proc(tmp_path, 4242, start_ticks=200)
    r = linux.process_get(4242)
    try:
        linux.process_get(4242, start_time=r["start_time"] + 9999)
    except LookupError:
        return
    pytest.fail("stale start_time must raise LookupError")


def test_dead_pid_rejected(linux):
    with pytest.raises(LookupError):
        linux.process_get(424242)


def test_pidfd_wait_preferred(linux, tmp_path, monkeypatch):
    import os
    calls = {"pidfd": 0}
    monkeypatch.setattr(os, "pidfd_open",
                        lambda pid: calls.__setitem__(
                            "pidfd", calls["pidfd"] + 1) or 0,
                        raising=False)
    fake_proc(tmp_path, 1, start_ticks=0)
    start = linux.process_get(1)["start_time"]
    try:
        linux.wait_process({"pid": 1, "start_time": start},
                           timeout_s=0.05)
    except Exception:
        pass
    assert calls["pidfd"] >= 1


def test_service_status_uses_fixed_argv(linux, monkeypatch):
    seen = []

    def fake_run(argv, **kw):
        seen.append(argv)
        return 0, b"active\n", b""

    monkeypatch.setattr(linux, "run_bounded", fake_run,
                        raising=False)
    monkeypatch.setattr(linux, "_systemd", lambda: True,
                        raising=False)
    r = linux.service_status("ssh.service")
    assert r["state"] == "active"
    assert seen and seen[0][0] == "systemctl"
    assert "ssh.service" in seen[0]
    assert not any(";" in str(a) for a in seen[0])


def test_service_name_injection_rejected(linux):
    with pytest.raises(Exception):
        linux.service_status("x; rm -rf /")
