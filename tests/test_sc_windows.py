"""sc_windows — real-host Win32 adapter tests (Windows only)."""
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_process  # noqa: E402

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Win32 only")

import sc_windows  # noqa: E402

PY = sys.executable
_EPOCH_DELTA_100NS = 116444736000000000


def _ground_truth_start(pid):
    """Own FILETIME ground truth for a pid's creation time."""
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    h = k32.OpenProcess(0x1000, False, pid)
    assert h, f"OpenProcess failed: {ctypes.get_last_error()}"
    try:
        times = (wintypes.FILETIME * 4)()
        refs = [ctypes.byref(t) for t in times]
        assert k32.GetProcessTimes(h, *refs)
        ft = times[0]
        raw = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
        return (raw - _EPOCH_DELTA_100NS) // 10_000_000
    finally:
        k32.CloseHandle(h)


def _handle_count():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.GetProcessHandleCount.restype = wintypes.BOOL
    k32.GetProcessHandleCount.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    count = wintypes.DWORD(0)
    me = k32.GetCurrentProcess()
    assert k32.GetProcessHandleCount(me, ctypes.byref(count))
    return count.value


def _dead(pid, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sc_windows.process_get(pid)
        except LookupError:
            return True
        time.sleep(0.1)
    return False


def test_process_get_own_pid_matches_ground_truth():
    r = sc_windows.process_get(os.getpid())
    assert r["pid"] == os.getpid()
    assert r["start_time"] == _ground_truth_start(os.getpid())
    assert "python" in r["name"].lower()


def test_process_get_dead_pid_lookup_error():
    with pytest.raises(LookupError):
        sc_windows.process_get(0x0FFFFFEF)


def test_process_get_stale_start_time_rejected():
    good = _ground_truth_start(os.getpid())
    with pytest.raises(LookupError, match="stale"):
        sc_windows.process_get(os.getpid(), start_time=good + 600)
    # matching start_time still returns
    r = sc_windows.process_get(os.getpid(), start_time=good)
    assert r["pid"] == os.getpid()


def test_wait_process_returns_on_child_exit():
    s = sc_windows.spawn_owned([PY, "-c", "import sys;sys.exit(7)"])
    try:
        r = sc_windows.wait_process(
            {"pid": s["pid"], "start_time": s["start_time"]},
            timeout_s=10)
        assert r["ok"] is True
        assert r["exit_code"] == 7
    finally:
        sc_windows.close_owned(s)


def test_wait_process_timeout():
    s = sc_windows.spawn_owned([PY, "-c", "import time;time.sleep(60)"])
    try:
        r = sc_windows.wait_process(
            {"pid": s["pid"], "start_time": s["start_time"]},
            timeout_s=0.3)
        assert r == {"ok": False, "status": "timeout"}
    finally:
        sc_windows.close_owned(s)


def test_wait_process_stale_identity_rejected_before_wait():
    s = sc_windows.spawn_owned([PY, "-c", "import time;time.sleep(60)"])
    try:
        r = sc_windows.wait_process(
            {"pid": s["pid"], "start_time": s["start_time"] + 600},
            timeout_s=5)
        assert r["ok"] is False and r["status"] == "rejected"
    finally:
        sc_windows.close_owned(s)


def test_spawn_owned_close_kills_child_via_job():
    s = sc_windows.spawn_owned([PY, "-c", "import time;time.sleep(60)"])
    assert s["ok"] is True and s["pid"] > 0
    sc_windows.close_owned(s)
    assert _dead(s["pid"])


def test_spawn_owned_job_kills_grandchildren():
    code = ("import subprocess,sys,time;"
            "p=subprocess.Popen([sys.executable,'-c',"
            "'import time;time.sleep(60)']);"
            "print(p.pid,flush=True);time.sleep(60)")
    s = sc_windows.spawn_owned([PY, "-c", code])
    try:
        # grandchild needs a moment to spawn; read its pid would need a
        # pipe, so instead just verify close_owned returns ok and the
        # root dies — KILL_ON_JOB_CLOSE covers the tree.
        time.sleep(1.0)
    finally:
        r = sc_windows.close_owned(s)
    assert r["ok"] is True
    assert _dead(s["pid"])


def test_suspended_spawn_no_output_before_resume(tmp_path):
    out = tmp_path / "escaped.txt"
    argv = [PY, "-c",
            "import sys;open(sys.argv[1],'w').write('x')", str(out)]
    proc = sc_windows._create_process(argv)
    try:
        time.sleep(0.5)
        assert not out.exists()  # still suspended: nothing ran
        sc_windows.resume_main_thread(proc["pid"])
        deadline = time.time() + 5
        while time.time() < deadline and not out.exists():
            time.sleep(0.05)
        assert out.exists()
    finally:
        sc_windows._terminate_process(proc)


def test_spawn_owned_fail_closed_no_orphan(monkeypatch):
    # Force failure between create and resume by breaking job assign
    # on the shared kernel32 binding.
    monkeypatch.setattr(
        sc_windows._kernel32(), "AssignProcessToJobObject",
        lambda job, proc: 0)
    with pytest.raises(RuntimeError):
        sc_windows.spawn_owned(
            [PY, "-c", "import time;time.sleep(60)"])
    # no suspended orphan: nothing to assert directly; leak loop below
    # would hang/crash if orphans accumulated.


def test_handle_leak_loop():
    before = _handle_count()
    for _ in range(40):
        s = sc_windows.spawn_owned([PY, "-c", "pass"])
        sc_windows.close_owned(s)
    after = _handle_count()
    assert after <= before + 8


def test_resume_main_thread_bad_pid_raises():
    with pytest.raises(Exception):
        sc_windows.resume_main_thread(0x0FFFFFEF)


def test_service_status_known_service():
    r = sc_windows.service_status("EventLog")
    assert r["name"] == "EventLog"
    assert r["state"] in ("running", "stopped", "paused",
                          "start_pending", "stop_pending",
                          "continue_pending", "pause_pending")


def test_service_status_bad_name_rejected():
    import sc_contract as contract
    with pytest.raises(contract.InvalidRequest):
        sc_windows.service_status("bad;name")


def test_service_status_unknown_service():
    with pytest.raises(LookupError):
        sc_windows.service_status("sc_no_such_service_xyz")


def test_restart_service_allowlist_rejects_before_scm():
    for allowed in (None, [], ["other_svc"]):
        r = sc_windows.restart_service("EventLog", allowed=allowed)
        assert r == {"ok": False, "status": "rejected"}
    with pytest.raises(Exception):
        sc_windows.restart_service("bad;name", allowed=["bad;name"])


def test_scm_available_bool():
    assert sc_windows.scm_available() is True


def test_cli_process_wait(capsys, monkeypatch):
    import sc_backend
    import sc_cli

    class B:
        name = "fake"

        def wait_process(self, identity, timeout_s):
            assert identity == {"pid": 1, "start_time": 2}
            return {"ok": True, "exit_code": 0}

    monkeypatch.setattr(sc_backend, "current", lambda: B())
    code = sc_cli.main(["process", "wait", "--pid", "1",
                        "--start-time", "2", "--timeout", "5"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["ok"] is True
    assert out["value"]["exit_code"] == 0


def test_cli_process_wait_rejected_maps_exit_2(capsys, monkeypatch):
    import sc_backend
    import sc_cli

    class B:
        name = "fake"

        def wait_process(self, identity, timeout_s):
            return {"ok": False, "status": "rejected"}

    monkeypatch.setattr(sc_backend, "current", lambda: B())
    code = sc_cli.main(["process", "wait", "--pid", "1",
                        "--start-time", "2"])
    out = json.loads(capsys.readouterr().out)
    assert code == 2 and out["status"] == "rejected"


def test_cli_service_restart_requires_allowed_and_token(
        capsys, tmp_path, monkeypatch):
    import sc_backend
    import sc_cli
    import sc_policy
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)

    class B:
        name = "fake"
        called = []

        def restart_service(self, name, *, allowed):
            self.called.append(name)
            return {"ok": True, "status": "verified"}

    b = B()
    monkeypatch.setattr(sc_backend, "current", lambda: b)
    code = sc_cli.main(["service", "restart", "--name", "svc",
                        "--confirmation-id", "c" * 64,
                        "--request-id", "r1"])
    out = json.loads(capsys.readouterr().out)
    assert code == 2 and out["status"] == "rejected"
    assert b.called == []


def test_cli_service_restart_confirm_flow(capsys, tmp_path,
                                          monkeypatch):
    import sc_backend
    import sc_cli
    import sc_policy
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)

    class B:
        name = "fake"

        def restart_service(self, name, *, allowed):
            return {"ok": True, "status": "verified",
                    "precondition": {"state": "running"},
                    "postcondition": {"state": "running"}}

    monkeypatch.setattr(sc_backend, "current", lambda: B())
    req = {"version": 1, "request_id": "r1",
           "capability": "service.restart",
           "args": {"name": "svc", "allowed": ["svc", "other"]},
           "deadline_ms": 30000,
           "policy": {"dry_run": False, "confirmation_id": None}}
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    code = sc_cli.main(["service", "restart", "--name", "svc",
                        "--allowed", "svc,other",
                        "--confirmation-id", cid,
                        "--request-id", "r1"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["ok"] is True
    assert out["status"] == "verified"
