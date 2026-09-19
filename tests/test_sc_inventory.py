"""sc_backend/sc_process — capability discovery and bounded inventory."""
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_backend  # noqa: E402
import sc_process as process  # noqa: E402
from backends import linux, macos, run_bounded, windows  # noqa: E402


class FakeBackend:
    name = "fake"
    def capabilities(self):
        return [
            {"name": "process.observe", "supported": True,
             "reason": None, "mode": "native"},
            {"name": "service.observe", "supported": True,
             "reason": None, "mode": "native"},
        ]
    def process_list(self, pid=None):
        return [{"pid": 7, "start_time": 99, "name": "worker"}]
    def process_get(self, pid, start_time=None):
        proc = self.process_list(pid)[0]
        if start_time is not None and proc["start_time"] != start_time:
            raise LookupError("stale pid identity")
        return proc
    def service_status(self, name):
        return {"name": name, "state": "running"}


def test_snapshot_is_bounded_and_typed():
    r = process.snapshot(limit=1, backend=FakeBackend())
    assert r["status"] == "verified"
    assert r["value"] == [{"pid": 7, "start_time": 99, "name": "worker"}]


def test_snapshot_generates_request_id_for_direct_callers():
    a = process.snapshot(backend=FakeBackend())
    b = process.snapshot(backend=FakeBackend())
    assert a["request_id"]
    assert b["request_id"]
    assert a["request_id"] != b["request_id"]


def test_snapshot_caps_limit():
    class Many(FakeBackend):
        def process_list(self, pid=None):
            return [{"pid": i, "start_time": i, "name": "p"}
                    for i in range(5)]
    r = process.snapshot(limit=2, backend=Many())
    assert len(r["value"]) == 2


def test_capabilities_returns_typed_entries():
    caps = sc_backend.capabilities(backend=FakeBackend())
    assert caps and all(
        set(c) >= {"name", "supported", "reason", "mode"}
        for c in caps)


def test_explicit_unsupported_capability():
    class Partial(FakeBackend):
        def capabilities(self):
            return [
                {"name": "process.observe", "supported": True,
                 "reason": None, "mode": "native"},
                {"name": "service.observe", "supported": False,
                 "reason": "systemd not detected", "mode": "none"},
            ]
    caps = sc_backend.capabilities(backend=Partial())
    svc = next(c for c in caps if c["name"] == "service.observe")
    assert svc["supported"] is False
    assert svc["reason"]


def test_unknown_platform_returns_unsupported_backend(monkeypatch):
    monkeypatch.setattr(sc_backend.platform, "system",
                        lambda: "Plan9")
    b = sc_backend.current()
    caps = b.capabilities()
    assert caps and all(c["supported"] is False for c in caps)
    with pytest.raises(sc_backend.BackendUnavailable):
        b.process_list()


def test_import_failure_returns_typed_unsupported(monkeypatch):
    real_import = sc_backend.importlib.import_module

    def boom(name, *a, **k):
        if name.endswith("windows"):
            raise ImportError("no win32")
        return real_import(name, *a, **k)

    monkeypatch.setattr(sc_backend.platform, "system",
                        lambda: "Windows")
    monkeypatch.setattr(sc_backend.importlib, "import_module", boom)
    b = sc_backend.current()
    caps = b.capabilities()
    assert caps and all(c["supported"] is False for c in caps)
    assert all(c["reason"] for c in caps)


def test_process_identity_requires_pid_and_start_time():
    b = FakeBackend()
    assert b.process_get(7, start_time=99)["pid"] == 7
    with pytest.raises(LookupError):
        b.process_get(7, start_time=1)  # stale pid reuse


def test_windows_process_list_parses_cim_dates(monkeypatch):
    """CIM JSON emits ISO-8601 under pwsh 7 and /Date(ms)/ under 5.1."""
    payload = json.dumps([
        {"ProcessId": 7,
         "CreationDate": "2026-09-19T09:19:34.550381-03:00",
         "Name": "w"},
        {"ProcessId": 8, "CreationDate": "/Date(1789820374550)/",
         "Name": "x"},
    ]).encode()
    monkeypatch.setattr(windows.shutil, "which", lambda n: "pwsh")
    monkeypatch.setattr(windows, "run_bounded",
                        lambda argv: (0, payload, b""))
    procs = windows.process_list()
    assert procs[0]["pid"] == 7 and procs[0]["start_time"] > 0
    assert procs[1]["start_time"] == 1789820374
    assert windows.process_get(8, start_time=1789820374)["pid"] == 8


def test_windows_unparseable_cim_date_fails_read(monkeypatch):
    payload = json.dumps([
        {"ProcessId": 7, "CreationDate": "not-a-date", "Name": "w"},
    ]).encode()
    monkeypatch.setattr(windows.shutil, "which", lambda n: "pwsh")
    monkeypatch.setattr(windows, "run_bounded",
                        lambda argv: (0, payload, b""))
    with pytest.raises(sc_backend.BackendUnavailable):
        windows.process_list()


def test_backends_reject_negative_identity():
    # Bound via the module under test (loader may hold a distinct
    # sc_contract instance).
    for mod in (windows, linux, macos):
        with pytest.raises(mod.InvalidRequest):
            mod.process_get(-1)
        with pytest.raises(mod.InvalidRequest):
            mod.process_get(7, start_time=-1)


def test_snapshot_rejects_negative_limit():
    with pytest.raises(process.contract.InvalidRequest):
        process.snapshot(limit=-1, backend=FakeBackend())


def test_service_name_validation_uses_invalid_request():
    # Bound via the module under test: loader may hold a distinct
    # sc_contract instance, so identity must come from the raiser.
    assert issubclass(windows.InvalidRequest, ValueError)
    for bad in ("bad;name", "svc && rm", ""):
        with pytest.raises(windows.InvalidRequest):
            windows.service_status(bad)
        with pytest.raises(linux.InvalidRequest):
            linux.service_status(bad)


def _fake_proc_tree(tmp_path, pids):
    stat = "7 (worker) S " + " ".join(["0"] * 18) + " 200 0"
    for pid in pids:
        d = tmp_path / str(pid)
        d.mkdir()
        (d / "stat").write_text(stat.replace("(worker)", f"(p{pid})"))


def test_linux_boot_time_read_once_per_scan(tmp_path, monkeypatch):
    _fake_proc_tree(tmp_path, [1, 2, 3])
    calls = []

    def fake_boot():
        calls.append(1)
        return 1000

    monkeypatch.setattr(linux, "_PROC", str(tmp_path))
    monkeypatch.setattr(linux, "_boot_time", fake_boot)
    monkeypatch.setattr(linux, "_clock_ticks", lambda: 100)
    procs = linux.process_list()
    assert len(procs) == 3
    assert calls == [1]
    assert all(p["start_time"] == 1002 for p in procs)


def test_run_bounded_caps_output_but_drains():
    code = ("import sys;"
            "sys.stdout.write('x'*200000);sys.stdout.flush();"
            "sys.stderr.write('y'*200000);sys.stderr.flush()")
    rc, out, err = run_bounded([sys.executable, "-c", code],
                               cap=1000, timeout=30)
    assert rc == 0
    assert len(out) == 1000 and len(err) == 1000
    assert out == b"x" * 1000


def test_run_bounded_timeout_kills_child():
    t0 = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        run_bounded([sys.executable, "-c",
                     "import time;time.sleep(60)"], timeout=1)
    assert time.monotonic() - t0 < 30  # killed+waited, not 60s
