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
    code, env = _run(capsys, "youtube", "trending")
    assert code == 1
    assert env["status"] == "missing"
    assert env["command"] == "youtube"


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
    for key in ("api_version", "status", "command", "stdout", "stderr",
                "duration_s", "meta"):
        assert key in env


def test_envelope_v2_provenance(capsys):
    code, env = _run(capsys, "bogus")
    assert code == 2
    assert env["api_version"] == 2
    answered = env["meta"]["answered_by"]
    assert answered["wrapper"] == "agent-reach"
    manifest = json.loads(
        (AR_DIR.parents[1] / "manifest.json").read_text(encoding="utf-8"))
    assert answered["bundle"] == manifest["version"]


def test_flag_injection_rejected(capsys, monkeypatch):
    monkeypatch.setattr(wrapper.shutil, "which", lambda n: n)
    code, env = _run(capsys, "youtube", "q", "--cookie", "jar")
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


def test_channel_maps_to_get(capsys, monkeypatch):
    captured = {}

    def fake_run(argv, command, timeout=wrapper.DEFAULT_TIMEOUT):
        captured["argv"] = argv
        return wrapper.envelope("ok", command, stdout="{}")

    monkeypatch.setattr(wrapper, "resolve_invoker", lambda: ["FAKE"])
    monkeypatch.setattr(wrapper, "run_cmd", fake_run)
    code, env = _run(capsys, "youtube.transcript", "VID123")
    assert code == 0
    assert captured["argv"][:3] == ["FAKE", "get", "youtube.transcript"]
    assert "VID123" in captured["argv"]
    assert "--json" in captured["argv"]


def test_rss_channel_maps_to_get(capsys, monkeypatch):
    captured = {}

    def fake_run(argv, command, timeout=wrapper.DEFAULT_TIMEOUT):
        captured["argv"] = argv
        return wrapper.envelope("ok", command, stdout="{}")

    monkeypatch.setattr(wrapper, "resolve_invoker", lambda: ["FAKE"])
    monkeypatch.setattr(wrapper, "run_cmd", fake_run)
    code, env = _run(capsys, "rss.feed", "https://x/feed")
    assert code == 0
    assert captured["argv"][1] == "get"
    assert captured["argv"][2] == "rss.feed"


def test_malformed_target_rejected(capsys):
    code, env = _run(capsys, "youtube.transcript.extra", "x")
    assert code == 2
    assert env["status"] == "rejected"


def test_doctor_uses_doctor_probe(capsys, monkeypatch):
    captured = {}

    def fake_run(argv, command, timeout=wrapper.DEFAULT_TIMEOUT):
        captured["argv"] = argv
        return wrapper.envelope("ok", command, stdout="[]")

    monkeypatch.setattr(wrapper, "resolve_invoker", lambda: ["FAKE"])
    monkeypatch.setattr(wrapper, "run_cmd", fake_run)
    code, env = _run(capsys, "doctor")
    assert code == 0
    assert env["status"] == "ok"
    assert captured["argv"] == ["FAKE", "doctor", "--json"]
    assert env["channels"] == []


def test_doctor_degraded_when_probe_fails(capsys, monkeypatch):
    def fake_run(argv, command, timeout=wrapper.DEFAULT_TIMEOUT):
        return wrapper.envelope("error", command,
                                stderr="channel down", exit_code=1)

    monkeypatch.setattr(wrapper, "resolve_invoker", lambda: ["FAKE"])
    monkeypatch.setattr(wrapper, "run_cmd", fake_run)
    code, env = _run(capsys, "doctor")
    assert code == 1
    assert env["status"] == "degraded"
    assert env["probe_exit_code"] == 1


def _run_standalone(tmp_path, manifest_content=None):
    """Copy wrapper.py alone into tmp_path, optionally with a manifest,
    and run it - exercises _bundle_version edge cases end-to-end."""
    import shutil
    import subprocess
    dst = tmp_path / "wrapper.py"
    shutil.copy(AR_DIR / "wrapper.py", dst)
    if manifest_content is not None:
        (tmp_path / "manifest.json").write_text(
            manifest_content, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(dst), "bogus"],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=30)
    return json.loads(proc.stdout)


def test_bundle_version_empty_without_manifest(tmp_path):
    env = _run_standalone(tmp_path)
    assert env["meta"]["answered_by"]["bundle"] == ""
    assert env["meta"]["answered_by"]["wrapper"] == "agent-reach"


def test_bundle_version_empty_on_malformed_manifest(tmp_path):
    env = _run_standalone(tmp_path, manifest_content="{not json")
    assert env["meta"]["answered_by"]["bundle"] == ""


def test_bundle_version_reads_manifest(tmp_path):
    env = _run_standalone(
        tmp_path, manifest_content='{"version": "9.9.9-test"}')
    assert env["meta"]["answered_by"]["bundle"] == "9.9.9-test"
