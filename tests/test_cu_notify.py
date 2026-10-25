"""Tests for the composite cu notification dispatch."""

import importlib.util
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTIFY = os.path.join(REPO, "extensions", "computer-use", "cu_notify.py")


@pytest.fixture
def mod(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("cu_notify", NOTIFY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "LOG", str(tmp_path / "cu_notifications.jsonl"))
    monkeypatch.delenv("CU_NOTIFY_WEBHOOK", raising=False)
    monkeypatch.delenv("CU_NOTIFY_HOOK", raising=False)
    return m


def test_file_adapter_always_on(mod, tmp_path):
    res = mod.notify("t", "hello", "warning")
    ok, path = res["_notify_file"]
    assert ok is True
    with open(path, encoding="utf-8") as f:
        rec = json.loads(f.readline())
    assert rec["title"] == "t" and rec["message"] == "hello"
    assert rec["level"] == "warning" and "ts" in rec


def test_webhook_and_script_skipped_unset(mod):
    res = mod.notify("t", "m")
    assert res["_notify_webhook"][0] is None
    assert res["_notify_script"][0] is None


def test_script_hook_runs(mod, monkeypatch, tmp_path):
    marker = tmp_path / "hook.txt"
    script = tmp_path / "hook.py"
    script.write_text(
        "import sys\nopen(%r, 'w').write(sys.argv[1] + '|' + sys.argv[3])\n"
        % str(marker))
    monkeypatch.setenv("CU_NOTIFY_HOOK",
                       f"{sys.executable} {script}")
    res = mod.notify("done", "body", "error")
    assert res["_notify_script"][0] is True
    assert marker.read_text() == "done|error"


def test_adapter_failure_never_blocks(mod, monkeypatch):
    monkeypatch.setenv("CU_NOTIFY_WEBHOOK", "http://127.0.0.1:1/dead")
    res = mod.notify("t", "m")
    assert res["_notify_file"][0] is True
    assert res["_notify_webhook"][0] is False


def test_cli(tmp_path, monkeypatch):
    env = dict(os.environ)
    proc = subprocess.run(
        [sys.executable, NOTIFY, "cli", "msg", "info"],
        capture_output=True, text=True, timeout=15, env=env)
    assert proc.returncode == 0
    assert "_notify_file" in proc.stdout
