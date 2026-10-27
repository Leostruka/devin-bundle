"""Contract tests for extensions/voicebox/wrapper.py.

All HTTP is monkeypatched; no real network access.
"""
import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "voicebox"))

import wrapper  # noqa: E402


def run_main(argv, capsys):
    with pytest.raises(SystemExit) as exc:
        sys.argv = ["wrapper.py"] + argv
        wrapper.main()
    out = capsys.readouterr().out
    return exc.value.code, json.loads(out)


class FakeResp:
    def __init__(self, status=200, body=b"", headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    def read(self, n=-1):
        return self._body


def test_backend_down_reports_missing(monkeypatch, capsys):
    def boom(req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(wrapper.urllib.request, "urlopen", boom)
    monkeypatch.delenv("VB_HOST", raising=False)

    code, env = run_main(["doctor"], capsys)
    assert code == 1
    assert env["status"] == "missing"
    assert env["action"] == "doctor"
    assert "hint" in env
    assert "python -m backend.main" in env["hint"]


def test_generate_happy_path(monkeypatch, capsys, tmp_path):
    captured = {}
    out_file = tmp_path / "line1.wav"

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResp(status=200, body=b"RIFF-fake-audio")

    monkeypatch.setattr(wrapper.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("VB_HOST", raising=False)

    code, env = run_main(
        ["generate", "--text", "hello world", "--voice", "narrator",
         "--engine", "xtts", "--out", str(out_file)], capsys)

    assert code == 0
    assert env["status"] == "ok"
    assert env["action"] == "generate"
    assert captured["url"] == "http://127.0.0.1:17493/generate"
    assert captured["method"] == "POST"
    assert captured["body"] == {"text": "hello world",
                              "voice": "narrator", "engine": "xtts"}
    assert captured["timeout"] == 300
    assert env["result"]["out"] == str(out_file)
    assert out_file.read_bytes() == b"RIFF-fake-audio"


def test_envelope_keys(monkeypatch, capsys):
    def fake_urlopen(req, timeout=None):
        return FakeResp(status=200, body=b'{"models": ["a"]}')

    monkeypatch.setattr(wrapper.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("VB_HOST", raising=False)

    code, env = run_main(["models"], capsys)
    assert code == 0
    for key in ("status", "action", "result", "duration_s"):
        assert key in env
    assert env["action"] == "models"


def test_vb_host_rejects_non_localhost(monkeypatch, capsys):
    monkeypatch.setenv("VB_HOST", "http://evil.example")

    code, env = run_main(["doctor"], capsys)
    assert code == 2
    assert env["status"] == "error"
    assert "localhost" in env["error"]


def test_vb_host_allows_localhost_override(monkeypatch, capsys):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        return FakeResp(status=200, body=b"{}")

    monkeypatch.setattr(wrapper.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("VB_HOST", "http://localhost:9999")

    code, env = run_main(["doctor"], capsys)
    assert code == 0
    assert captured["url"].startswith("http://localhost:9999")
