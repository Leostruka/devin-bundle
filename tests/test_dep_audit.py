"""dep-audit.py + dep-audit-gate.py contract tests (no network, stubbed scanners)."""
import importlib.util
import io
import json
import os
import sys
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


audit = _load("dep_audit", "dep-audit.py")
gate = _load("dep_audit_gate", "dep-audit-gate.py")


def test_detect_ecosystems(tmp_path):
    (tmp_path / "requirements.txt").write_text("requests\n")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "Cargo.toml").write_text("[package]\n")
    assert set(audit._detect(str(tmp_path))) == {"python", "node", "rust"}


def test_detect_empty(tmp_path):
    assert audit._detect(str(tmp_path)) == []


def test_scan_no_scanners_skips(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("requests\n")
    monkeypatch.setattr(audit.shutil, "which", lambda n: None)
    out = audit.scan(str(tmp_path))
    assert out["ok"] is True
    assert out["detected"] == ["python"]
    assert out["scanned"] == []
    assert out["skipped"][0]["ecosystem"] == "python"


def test_pip_audit_parse(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("requests\n")
    payload = [{"name": "requests", "vulns": [
        {"id": "CVE-2024-0001", "severity": "HIGH",
         "fix_versions": ["2.32.0"]}]}]

    class P:
        returncode = 1
        stdout = json.dumps(payload)
        stderr = ""

    monkeypatch.setattr(audit.shutil, "which",
                        lambda n: "/usr/bin/pip-audit" if n == "pip-audit" else None)
    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: P())
    res, err = audit._pip_audit(str(tmp_path))
    assert err is None
    f = res["findings"][0]
    assert f["pkg"] == "requests" and f["id"] == "CVE-2024-0001"
    assert f["severity"] == "high" and f["fixed_in"] == ["2.32.0"]


def test_npm_audit_parse(tmp_path, monkeypatch):
    payload = {"vulnerabilities": {"lodash": {
        "severity": "high",
        "via": [{"url": "https://github.com/advisories/GHSA-xxxx"}],
        "fixAvailable": {"version": "4.17.21"}}}}

    class P:
        returncode = 1
        stdout = json.dumps(payload)
        stderr = ""

    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: P())
    res, err = audit._npm_audit(str(tmp_path))
    assert err is None
    f = res["findings"][0]
    assert f["pkg"] == "lodash" and f["id"] == "GHSA-xxxx"
    assert f["severity"] == "high" and f["fixed_in"] == "4.17.21"


def _gate_run(payload, scanners=("pip-audit",)):
    out = io.StringIO()
    env = {"DEVIN_PROJECT_DIR": os.getcwd()}
    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         patch.dict(os.environ, env), \
         patch.object(gate.shutil, "which",
                      lambda n: "/x" if n in scanners else None), \
         patch.object(gate.subprocess, "run") as run:
        run.return_value = type("P", (), {
            "stdout": json.dumps({"ok": True, "scanned": [
                {"findings": [{"pkg": "requests", "id": "CVE-1"}]}],
             "skipped": [], "errors": []}),
            "stderr": "", "returncode": 0})()
        import contextlib
        with contextlib.suppress(SystemExit):
            gate.main()
        return out.getvalue(), run.called


def test_gate_ignores_non_exec():
    out, called = _gate_run({"tool_name": "write", "tool_input": {}})
    assert out == "" and called is False


def test_gate_ignores_non_install():
    out, called = _gate_run({"tool_name": "exec",
                             "tool_input": {"command": "git status"}})
    assert out == "" and called is False


def test_gate_ignores_without_scanners():
    out, called = _gate_run(
        {"tool_name": "exec",
         "tool_input": {"command": "pip install requests"}},
        scanners=())
    assert out == "" and called is False


def test_gate_warns_on_findings():
    out, called = _gate_run(
        {"tool_name": "exec",
         "tool_input": {"command": "npm install lodash"}})
    assert called is True
    data = json.loads(out)
    ctx = data["hookSpecificOutput"]["additionalContext"]
    assert "[DEP-AUDIT]" in ctx and "requests:CVE-1" in ctx


def test_gate_silent_on_clean():
    out = io.StringIO()
    payload = {"tool_name": "exec",
               "tool_input": {"command": "pip install requests"}}
    clean = {"ok": True, "scanned": [{"findings": []}],
             "skipped": [], "errors": []}

    class P:
        stdout = json.dumps(clean)
        stderr = ""
        returncode = 0

    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         patch.dict(os.environ, {"DEVIN_PROJECT_DIR": os.getcwd()}), \
         patch.object(gate.shutil, "which", lambda n: "/x"), \
         patch.object(gate.subprocess, "run", lambda *a, **k: P()):
        import contextlib
        with contextlib.suppress(SystemExit):
            gate.main()
    assert out.getvalue() == ""


# --- issue #404: INSTALL_RE coverage + hook-budget timeout ---

@pytest.mark.parametrize("cmd", [
    "python -m pip install requests",
    "python3.11 -m pip install -r req.txt",
    "py -m pip install requests",
    "pipx install httpie",
    "uv add requests",
    "uv pip install requests",
    "poetry add requests",
    "pipenv install",
    "conda install numpy",
    "bundle install",
    "gem install rails",
    "mix deps.get",
    "dotnet add package Foo",
    "dotnet tool install -g dotnet-ef",
    "composer global require phpunit/phpunit",
    "sudo npm install lodash",
    "cd app && cargo add serde",
])
def test_install_re_matches(cmd):
    assert gate.INSTALL_RE.search(cmd), cmd


@pytest.mark.parametrize("cmd", [
    "pip list",
    "pip freeze",
    "gem list",
    "bundle exec rspec",
    "mix test",
    "dotnet build",
    "dotnet run",
    "npm ls",
    "cargo build",
    "git status",
])
def test_install_re_ignores_non_install(cmd):
    assert not gate.INSTALL_RE.search(cmd), cmd


def test_gate_scan_bounded_by_hook_budget():
    """Gate must pass --max-seconds and stay under the 35s hook timeout
    (issue #404: 300s child timeout could never finish inside budget)."""
    out = io.StringIO()
    payload = {"tool_name": "exec",
               "tool_input": {"command": "pip install requests"}}
    clean = {"ok": True, "scanned": [{"findings": []}],
             "skipped": [], "errors": []}

    class P:
        stdout = json.dumps(clean)
        stderr = ""
        returncode = 0

    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         patch.dict(os.environ, {"DEVIN_PROJECT_DIR": os.getcwd()}), \
         patch.object(gate.shutil, "which", lambda n: "/x"), \
         patch.object(gate.subprocess, "run") as run:
        run.return_value = P()
        import contextlib
        with contextlib.suppress(SystemExit):
            gate.main()
    argv = run.call_args[0][0]
    assert "--max-seconds" in argv
    assert argv[argv.index("--max-seconds") + 1] == "28"
    assert run.call_args[1]["timeout"] <= 33


def test_dep_audit_max_seconds_skips_exhausted(tmp_path, monkeypatch):
    """--max-seconds=0 exhausts budget immediately: detected ecosystems
    are skipped 'budget-exhausted', never scanned."""
    (tmp_path / "requirements.txt").write_text("requests\n")
    (tmp_path / "package.json").write_text("{}")
    monkeypatch.setattr(audit.shutil, "which",
                        lambda n: "/x" if n in ("pip-audit", "npm") else None)
    out = audit.scan(str(tmp_path), max_seconds=0)
    assert out["ok"] is True
    assert out["scanned"] == []
    reasons = {s["ecosystem"]: s["reason"] for s in out["skipped"]}
    assert reasons.get("python") == "budget-exhausted"
    assert reasons.get("node") == "budget-exhausted"


def test_deadline_caps_scanner_timeout():
    dl = audit._Deadline(5)
    assert dl.cap(300) <= 5
    assert audit._Deadline(None).cap(300) == 300
