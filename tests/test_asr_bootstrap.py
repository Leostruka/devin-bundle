"""asr/bootstrap.py - hardening contract (audit-r4 issue 02)."""
import io
import json
import sys
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

ASR = Path(__file__).resolve().parents[1] / "extensions" / "asr"
sys.path.insert(0, str(ASR))

import bootstrap  # noqa: E402


def test_model_arg_traversal_rejected(capsys):
    rc = bootstrap.main(["--model", "a/../../evil"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False and "bad_model" in out["error"]


def test_model_arg_slash_rejected(capsys):
    rc = bootstrap.main(["--model", "sub/dir"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2 and "bad_model" in out["error"]


def test_fetch_error_typed(monkeypatch, capsys):
    def _boom(req, timeout=None):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", _boom)
    rc = bootstrap.main(["--skip-binary", "--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["error"].startswith("fetch_error:")


def test_bad_zip_typed(monkeypatch, capsys):
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: b"not a zip")
    rc = bootstrap.main(["--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert "bad_archive" in out["error"]


def _zip_with(member_name):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(member_name, b"x")
        z.writestr("ok/main.exe", b"bin")
    return buf.getvalue()


def test_zip_slip_member_rejected(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: _zip_with("../evil.exe"))
    orig = bootstrap.CACHE
    bootstrap.CACHE = tmp_path / "_cache"
    try:
        rc = bootstrap.main(["--model", "base"])
    finally:
        bootstrap.CACHE = orig
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert "unsafe_member" in out["error"]
    assert not (tmp_path.parent / "evil.exe").exists()
    assert not (tmp_path / "evil.exe").exists()


def test_safe_zip_extracts(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    calls = {"n": 0}

    def _fetch(url):
        calls["n"] += 1
        if calls["n"] == 1:
            return _zip_with("Release/main.exe")
        return b"model-bytes"
    monkeypatch.setattr(bootstrap, "_fetch", _fetch)
    orig = bootstrap.CACHE
    bootstrap.CACHE = tmp_path / "_cache"
    try:
        rc = bootstrap.main(["--model", "base"])
    finally:
        bootstrap.CACHE = orig
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"]
    assert (tmp_path / "_cache" / "Release" / "main.exe").exists()
    assert (tmp_path / "_cache" / "ggml-base.bin").read_bytes() == \
        b"model-bytes"
