"""agent-reach wrapper contract tests -- no network, no real CLI."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

AR_DIR = Path(__file__).resolve().parents[1] / "extensions" / "agent-reach"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wrapper = _load("agent_reach_wrapper", AR_DIR / "wrapper.py")


def _run(capsys, *argv):
    with pytest.raises(SystemExit) as exc:
        wrapper.main(list(argv))
    out = capsys.readouterr().out.strip()
    payload = json.loads(out) if out else None
    return exc.value.code, payload


def test_missing_binary_reports_missing(capsys, monkeypatch):
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: None)
    code, env = _run(capsys, "github", "trending")
    assert code == 1
    assert env["status"] == "missing"
    assert env["command"] == "github"


def test_doctor_missing_toolchain(capsys, monkeypatch):
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: None)
    code, env = _run(capsys, "doctor")
    assert code == 1
    assert env["status"] == "missing"


def test_unknown_channel_rejected(capsys):
    code, env = _run(capsys, "myspace")
    assert code == 2
    assert env["status"] == "rejected"
    assert "myspace" in env["stderr"]


@pytest.mark.parametrize("chan", ["twitter", "x", "reddit", "instagram",
                                  "xiaohongshu", "boss"])
def test_credentialed_channels_rejected(capsys, chan):
    code, env = _run(capsys, chan, "query")
    assert code == 2
    assert env["status"] == "rejected"
    assert "credential" in env["stderr"] or "cookie" in env["stderr"] \
        or "credentials" in env["stderr"]
    assert env["command"] == chan


def test_envelope_keys_present(capsys):
    code, env = _run(capsys, "bogus")
    assert code == 2
    for key in ("status", "command", "stdout", "stderr", "duration_s"):
        assert key in env


def test_flag_injection_rejected(capsys, monkeypatch):
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: n)
    code, env = _run(capsys, "web", "http://x", "--cookie", "jar")
    assert code == 2
    assert env["status"] == "rejected"


def test_channel_runs_with_fake_invoker(capsys, monkeypatch):
    monkeypatch.setattr(wrapper, "resolve_invoker",
                        lambda: [sys.executable, "-c",
                                 "import sys; print('trends')"])
    code, env = _run(capsys, "youtube", "lofi")
    assert code == 0
    assert env["status"] == "ok"
    assert "trends" in env["stdout"]
