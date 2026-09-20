"""sc_cli — one JSON object on stdout; exit 0 verified, 1 runtime, 2 rejected."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_backend  # noqa: E402
import sc_cli  # noqa: E402
import sc_policy  # noqa: E402


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


def _preflight_req(capability):
    return json.dumps({
        "version": 1, "request_id": "r1", "capability": capability,
        "args": {}, "deadline_ms": 1000,
        "policy": {"dry_run": False}})


def test_cli_preflight_allow(capsys):
    code, r, _ = _run(["preflight", _preflight_req("capabilities")],
                      capsys)
    assert code == 0 and r["status"] == "verified"
    assert r["value"] == {"decision": "allow",
                          "reason": "capability_allowed"}


def test_cli_preflight_confirm(capsys):
    code, r, _ = _run(["preflight", _preflight_req("process.cancel")],
                      capsys)
    assert code == 0
    assert r["value"] == {"decision": "confirm",
                          "reason": "confirmation_required"}


def test_cli_preflight_deny(capsys):
    code, r, _ = _run(["preflight", _preflight_req("file.delete")],
                      capsys)
    assert code == 0
    assert r["value"] == {"decision": "deny",
                          "reason": "capability_denied"}


def test_cli_preflight_unknown_capability_denied(capsys):
    code, r, _ = _run(["preflight", _preflight_req("nope.nope")],
                      capsys)
    assert code == 0
    assert r["value"]["reason"] == "unknown_capability"


def test_cli_preflight_invalid_json_rejected(capsys):
    code, r, _ = _run(["preflight", "{not json"], capsys)
    assert code == 2 and r["status"] == "rejected"
    assert r["backend"] == "policy"


def test_cli_preflight_invalid_request_rejected(capsys):
    bad = json.dumps({"version": 2, "request_id": "r",
                      "capability": "capabilities", "args": {},
                      "deadline_ms": 1000})
    code, r, _ = _run(["preflight", bad], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_preflight_does_not_need_backend(capsys, monkeypatch):
    def boom():
        raise RuntimeError("backend discovery failed")
    monkeypatch.setattr(sc_backend, "current", boom)
    code, r, _ = _run(["preflight", _preflight_req("capabilities")],
                      capsys)
    assert code == 0 and r["status"] == "verified"
    assert r["backend"] == "policy"
    assert r["value"] == {"decision": "allow",
                          "reason": "capability_allowed"}


def test_cli_preflight_exactly_one_positional(capsys):
    code, r, _ = _run(["preflight"], capsys)
    assert code == 2 and r["status"] == "rejected"
    assert r["backend"] == "policy"
    code, r, _ = _run(["preflight", _preflight_req("capabilities"),
                       "extra"], capsys)
    assert code == 2 and r["status"] == "rejected"
    assert r["backend"] == "policy"


def _exec_request(request_id, argv, cwd=None, timeout_s=30):
    return {
        "version": 1, "request_id": request_id,
        "capability": "process.exec",
        "args": {"argv": argv, "cwd": cwd, "timeout_s": timeout_s},
        "deadline_ms": max(1, int(timeout_s * 1000)),
        "policy": {"dry_run": False, "confirmation_id": None}}


def _exec_argv(argv, request_id="r1", cid="c", timeout=None, cwd=None):
    args = ["exec", "--argv-json", json.dumps(argv),
            "--request-id", request_id, "--confirmation-id", cid]
    if timeout is not None:
        args += ["--timeout", str(timeout)]
    if cwd is not None:
        args += ["--cwd", cwd]
    return args


def test_cli_exec_requires_confirmation(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)
    argv = [sys.executable, "-c", "pass"]
    code, r, _ = _run(_exec_argv(argv, cid="f" * 64), capsys)
    assert code == 2 and r["status"] == "rejected"
    code, r, _ = _run(_exec_argv(argv, cid="not-a-token"), capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_exec_consumed_confirmation_runs_once(
        capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)
    argv = [sys.executable, "-c", "print('ok')"]
    req = _exec_request("r1", argv)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    code, r, _ = _run(_exec_argv(argv, cid=cid), capsys)
    assert code == 0 and r["status"] == "dispatched"
    assert r["request_id"] == "r1"
    assert r["backend"] == "subprocess"
    assert r["value"]["stdout"]["value"].strip() == "ok"
    # replay rejects before spawn
    code, r, _ = _run(_exec_argv(argv, cid=cid), capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_exec_mutation_rejected_before_spawn(
        capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)
    argv = [sys.executable, "-c", "pass"]
    for mutate_argv, mutate_kw in (
            ([sys.executable, "-c", "print(1)"], {}),
            (argv, {"timeout": 10}),
            (argv, {"cwd": str(tmp_path)}),
            (argv, {})):
        req = _exec_request("r1", argv)
        cid = sc_policy.issue_confirmation(req)["confirmation_id"]
        rid = "r2" if mutate_kw == {} and mutate_argv == argv else "r1"
        code, r, _ = _run(_exec_argv(mutate_argv, request_id=rid,
                                     cid=cid, **mutate_kw), capsys)
        assert code == 2 and r["status"] == "rejected"


def test_cli_exec_flag_validation(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)
    argv = json.dumps([sys.executable, "-c", "pass"])
    for args in (
            ["exec"],
            ["exec", "--argv-json", argv],
            ["exec", "--argv-json", argv, "--request-id", "r"],
            ["exec", "--argv-json", argv, "--request-id", "r",
             "--confirmation-id", "c", "--bogus", "1"],
            ["exec", "--argv-json", argv, "--argv-json", argv,
             "--request-id", "r", "--confirmation-id", "c"],
            ["exec", "positional", "--argv-json", argv,
             "--request-id", "r", "--confirmation-id", "c"]):
        code, r, _ = _run(args, capsys)
        assert code == 2 and r["status"] == "rejected", args


def test_cli_exec_bad_argv_json_rejected(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)
    code, r, _ = _run(
        ["exec", "--argv-json", "{bad", "--request-id", "r",
         "--confirmation-id", "c" * 64], capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_exec_invalid_input_never_consumes_token(
        capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path)
    argv = [sys.executable, "-c", "print('ok')"]
    req = _exec_request("r1", argv)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    # invalid argv / cwd / timeout each reject before consumption
    for bad_args in (
            _exec_argv('"ls"', cid=cid),
            _exec_argv(argv, cid=cid, cwd=str(tmp_path / "missing")),
            _exec_argv(argv, cid=cid, timeout=999),
            _exec_argv(argv, cid=cid, timeout="nan")):
        code, r, _ = _run(bad_args, capsys)
        assert code == 2 and r["status"] == "rejected", bad_args
        assert (tmp_path / f"{cid}.json").exists()  # not consumed
    # the same token still works for the exact confirmed request
    code, r, _ = _run(_exec_argv(argv, cid=cid), capsys)
    assert code == 0 and r["status"] == "dispatched"
