"""sc_cli — one JSON object on stdout; exit 0 verified, 1 runtime, 2 rejected."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_backend  # noqa: E402
import sc_cli  # noqa: E402


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


@pytest.fixture(autouse=True)
def _fake_backend(monkeypatch):
    monkeypatch.setattr(sc_backend, "current", lambda: FakeBackend())
    monkeypatch.setattr(sc_cli, "sc_backend", sc_backend)


def _run(argv, capsys):
    code = sc_cli.main(argv)
    out = capsys.readouterr().out.strip()
    return code, json.loads(out), out


def test_cli_capabilities_prints_one_json(capsys):
    code, r, raw = _run(["capabilities"], capsys)
    assert code == 0
    assert r["ok"] is True and r["status"] == "verified"
    assert isinstance(r["value"], list)
    json.loads(raw)  # exactly one JSON object


def test_cli_process_list(capsys):
    code, r, _ = _run(["process-list"], capsys)
    assert code == 0
    assert r["status"] == "verified"
    assert r["value"] == [
        {"pid": 7, "start_time": 99, "name": "worker"}]


def test_cli_process_get_requires_start_time(capsys):
    code, r, _ = _run(["process-get", "--pid", "7"], capsys)
    assert code == 2
    assert r["ok"] is False and r["status"] == "rejected"


def test_cli_process_get_verified(capsys):
    code, r, _ = _run(
        ["process-get", "--pid", "7", "--start-time", "99"], capsys)
    assert code == 0
    assert r["value"]["pid"] == 7
    assert r["value"]["start_time"] == 99


def test_cli_process_get_stale_identity_rejected(capsys):
    code, r, _ = _run(
        ["process-get", "--pid", "7", "--start-time", "1"], capsys)
    assert code == 2
    assert r["ok"] is False and r["status"] == "rejected"
    assert r["backend"] == "fake"
    assert r["error"]


def test_cli_process_get_not_found_rejected(capsys, monkeypatch):
    def missing(pid, start_time=None):
        raise LookupError("process not found")
    monkeypatch.setattr(FakeBackend, "process_get",
                        staticmethod(missing))
    code, r, _ = _run(
        ["process-get", "--pid", "7", "--start-time", "99"], capsys)
    assert code == 2
    assert r["status"] == "rejected"
    assert r["backend"] == "fake"
    assert "not found" in r["error"]


def test_cli_rejects_negative_identity_and_limit(capsys):
    for argv in (
            ["process-get", "--pid", "-1", "--start-time", "9"],
            ["process-get", "--pid", "7", "--start-time", "-1"],
            ["process-list", "--pid", "-1"],
            ["process-list", "--limit", "-1"]):
        code, r, _ = _run(argv, capsys)
        assert code == 2 and r["status"] == "rejected", argv


def test_cli_service_status(capsys):
    code, r, _ = _run(["service-status", "w32time"], capsys)
    assert code == 0
    assert r["value"] == {"name": "w32time", "state": "running"}


def test_cli_unknown_command_rejected(capsys):
    code, r, raw = _run(["bogus-cmd"], capsys)
    assert code == 2
    assert r["ok"] is False and r["status"] == "rejected"
    json.loads(raw)  # still exactly one JSON object


def test_cli_runtime_failure_exit_1(capsys, monkeypatch):
    def boom(pid=None):
        raise RuntimeError("wmi dead")
    monkeypatch.setattr(FakeBackend, "process_list",
                        staticmethod(boom))
    code, r, _ = _run(["process-list"], capsys)
    assert code == 1
    assert r["ok"] is False


def test_cli_missing_args_rejected(capsys):
    code, r, _ = _run(["service-status"], capsys)
    assert code == 2
    assert r["status"] == "rejected"


def test_cli_backend_valueerror_is_runtime_not_rejected(capsys,
                                                        monkeypatch):
    """Malformed backend output → exit 1, never confused with bad input."""
    def boom(pid=None):
        raise ValueError("garbage /proc/stat")
    monkeypatch.setattr(FakeBackend, "process_list",
                        staticmethod(boom))
    code, r, _ = _run(["process-list"], capsys)
    assert code == 1
    assert r["ok"] is False and r["status"] != "rejected"


def test_cli_backend_error_keeps_backend_name(capsys, monkeypatch):
    def boom(pid=None):
        raise RuntimeError("wmi dead")
    monkeypatch.setattr(FakeBackend, "process_list",
                        staticmethod(boom))
    code, r, _ = _run(["process-list"], capsys)
    assert code == 1
    assert r["backend"] == "fake"


def test_cli_subprocess_timeout_maps_to_timeout(capsys, monkeypatch):
    import subprocess

    def hang(pid=None):
        raise subprocess.TimeoutExpired(["ps"], 10)
    monkeypatch.setattr(FakeBackend, "process_list",
                        staticmethod(hang))
    code, r, _ = _run(["process-list"], capsys)
    assert code == 1
    assert r["status"] == "timeout"


def test_cli_invalid_request_validation_exit_2(capsys, monkeypatch):
    # Raise via sc_cli's own contract module so the class identity
    # matches its except clause regardless of test loader ordering.
    def bad_name(name):
        raise sc_cli.contract.InvalidRequest("invalid service name")
    monkeypatch.setattr(FakeBackend, "service_status",
                        staticmethod(bad_name))
    code, r, _ = _run(["service-status", "bad;name"], capsys)
    assert code == 2
    assert r["status"] == "rejected"


def test_cli_rejects_trailing_args(capsys):
    code, r, _ = _run(["capabilities", "extra"], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_rejects_unknown_flag(capsys):
    code, r, _ = _run(["process-list", "--bogus", "1"], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_rejects_duplicate_flag(capsys):
    code, r, _ = _run(
        ["process-list", "--pid", "1", "--pid", "2"], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_rejects_extra_positional(capsys):
    code, r, _ = _run(["service-status", "a", "b"], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_rejects_non_integer_flag(capsys):
    code, r, _ = _run(["process-get", "--pid", "abc",
                       "--start-time", "9"], capsys)
    assert code == 2 and r["status"] == "rejected"
