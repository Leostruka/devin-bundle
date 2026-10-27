"""hyperframes wrapper contract tests -- no network, no real npx."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HF_DIR = Path(__file__).resolve().parents[1] / "extensions" / "hyperframes"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wrapper = _load("hyperframes_wrapper", HF_DIR / "wrapper.py")


def _run(capsys, *argv):
    """Invoke wrapper.main(argv); return (exit_code, parsed_json_or_None)."""
    with pytest.raises(SystemExit) as exc:
        wrapper.main(list(argv))
    out = capsys.readouterr().out.strip()
    payload = json.loads(out) if out else None
    return exc.value.code, payload


def test_missing_binary_reports_missing(capsys, monkeypatch):
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: None)
    code, env = _run(capsys, "render", "proj/")
    assert code == 1
    assert env["status"] == "missing"
    assert env["command"] == "render"


def test_doctor_missing_toolchain(capsys, monkeypatch):
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: None)
    code, env = _run(capsys, "doctor")
    assert code == 1
    assert env["status"] == "missing"
    assert env["node_ok"] is False


def test_unknown_subcommand_rejected(capsys):
    code, env = _run(capsys, "publish")
    assert code == 2
    assert env["status"] == "rejected"
    assert "publish" in env["stderr"]


def test_flag_injection_rejected(capsys):
    for argv in (
        ("render", "proj/", "--exec", "rm -rf /"),
        ("render", "proj/", "--plugins=x"),
        ("render", "proj/", "-e"),
    ):
        code, env = _run(capsys, *argv)
        assert code == 2
        assert env["status"] == "rejected"


def test_render_requires_input(capsys):
    code, env = _run(capsys, "render")
    assert code == 2
    assert env["status"] == "rejected"
    assert "input" in env["stderr"] or "project path" in env["stderr"]


def test_envelope_keys_present(capsys):
    code, env = _run(capsys, "bogus")
    assert code == 2
    for key in ("status", "command", "stdout", "stderr", "duration_s"):
        assert key in env


def test_whitelisted_flags_parse(capsys, monkeypatch):
    """Whitelisted flags pass validation; then invoker-missing fires."""
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: None)
    code, env = _run(
        capsys, "render", "proj/", "--output", "out.mp4",
        "--fps", "30", "--duration", "5", "--width", "1280",
        "--height", "720")
    assert code == 1
    assert env["status"] == "missing"


def test_render_runs_with_fake_invoker(capsys, monkeypatch):
    monkeypatch.setattr(wrapper, "resolve_invoker",
                        lambda: [sys.executable, "-c",
                                 "import sys; print('rendered')"])
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: n)
    code, env = _run(capsys, "render", "--input", "proj/",
                     "--output", "out.mp4")
    assert code == 0
    assert env["status"] == "ok"
    assert "rendered" in env["stdout"]
