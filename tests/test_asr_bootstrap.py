"""asr/bootstrap.py - hardening contract (audit-r4 issue 02)."""
import hashlib
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


def _pin_hashes(monkeypatch, release_bytes=None, model_bytes=None):
    """Point the pinned digests at the fake payloads so checksum
    verification passes and the flow reaches the code under test."""
    if release_bytes is not None:
        monkeypatch.setattr(bootstrap, "RELEASE_SHA256",
                            hashlib.sha256(release_bytes).hexdigest())
    if model_bytes is not None:
        monkeypatch.setitem(
            bootstrap.MODEL_SHA256, "base",
            hashlib.sha256(model_bytes).hexdigest())


def test_model_arg_traversal_rejected(capsys):
    rc = bootstrap.main(["--model", "a/../../evil"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False and "bad_model" in out["error"]


def test_model_arg_slash_rejected(capsys):
    rc = bootstrap.main(["--model", "sub/dir"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2 and "bad_model" in out["error"]


def test_fetch_error_typed(monkeypatch, capsys, tmp_path):
    def _boom(req, timeout=None):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", _boom)
    monkeypatch.setattr(bootstrap, "CACHE", tmp_path / "_cache")
    rc = bootstrap.main(["--skip-binary", "--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["error"].startswith("fetch_error:")


def test_unpinned_model_rejected(capsys):
    rc = bootstrap.main(["--model", "medium"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False and "unpinned_model" in out["error"]


def test_release_checksum_mismatch(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    monkeypatch.setattr(bootstrap, "CACHE", tmp_path / "_cache")
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: b"tampered-zip-bytes")
    rc = bootstrap.main(["--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert "checksum_mismatch" in out["error"]


def test_cached_model_skips_fetch(monkeypatch, tmp_path, capsys):
    cache = tmp_path / "_cache"
    cache.mkdir()
    good = b"verified-model-bytes"
    _pin_hashes(monkeypatch, model_bytes=good)
    (cache / "ggml-base.bin").write_bytes(good)
    calls = []
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: calls.append(url) or b"x")
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Linux")
    monkeypatch.setattr(bootstrap, "CACHE", cache)
    rc = bootstrap.main(["--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"]
    assert calls == []
    assert any("already cached" in s for s in out["steps"])


def test_corrupt_cached_model_refetches(monkeypatch, tmp_path, capsys):
    cache = tmp_path / "_cache"
    cache.mkdir()
    good = b"good-model-bytes"
    _pin_hashes(monkeypatch, model_bytes=good)
    (cache / "ggml-base.bin").write_bytes(b"corrupt")
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: good)
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Linux")
    monkeypatch.setattr(bootstrap, "CACHE", cache)
    rc = bootstrap.main(["--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"]
    assert (cache / "ggml-base.bin").read_bytes() == good


def test_binary_marker_skips_refetch(monkeypatch, tmp_path, capsys):
    cache = tmp_path / "_cache"
    cache.mkdir()
    (cache / bootstrap.BIN_MARKER).write_text("x", encoding="utf-8")
    good = b"model-bytes"
    _pin_hashes(monkeypatch, model_bytes=good)
    calls = []
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: calls.append(url) or good)
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    monkeypatch.setattr(bootstrap, "CACHE", cache)
    rc = bootstrap.main(["--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"]
    # only the model fetch happened - binary skipped via marker
    assert len(calls) == 1
    assert "huggingface" in calls[0]


def test_bad_zip_typed(monkeypatch, tmp_path, capsys):
    bad = b"not a zip"
    _pin_hashes(monkeypatch, release_bytes=bad)
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    monkeypatch.setattr(bootstrap, "CACHE", tmp_path / "_cache")
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: bad if "github" in url else b"m")
    _pin_hashes(monkeypatch, model_bytes=b"m")
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
    evil = _zip_with("../evil.exe")
    _pin_hashes(monkeypatch, release_bytes=evil)
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    monkeypatch.setattr(bootstrap, "_fetch",
                        lambda url: evil if "github" in url else b"m")
    _pin_hashes(monkeypatch, model_bytes=b"m")
    monkeypatch.setattr(bootstrap, "CACHE", tmp_path / "_cache")
    rc = bootstrap.main(["--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert "unsafe_member" in out["error"]
    assert not (tmp_path.parent / "evil.exe").exists()
    assert not (tmp_path / "evil.exe").exists()


def test_safe_zip_extracts(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bootstrap.platform, "system",
                        lambda: "Windows")
    zbytes = _zip_with("Release/main.exe")
    model = b"model-bytes"
    _pin_hashes(monkeypatch, release_bytes=zbytes, model_bytes=model)
    calls = {"n": 0}

    def _fetch(url):
        calls["n"] += 1
        return zbytes if calls["n"] == 1 else model
    monkeypatch.setattr(bootstrap, "_fetch", _fetch)
    monkeypatch.setattr(bootstrap, "CACHE", tmp_path / "_cache")
    rc = bootstrap.main(["--model", "base"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"]
    assert (tmp_path / "_cache" / "Release" / "main.exe").exists()
    assert (tmp_path / "_cache" / "ggml-base.bin").read_bytes() == model
    # marker recorded so a re-run skips the binary fetch
    assert (tmp_path / "_cache" / bootstrap.BIN_MARKER).exists()


def test_transcribe_model_path_variants(tmp_path, monkeypatch):
    """Issue #430: ggml filenames + medium/large resolve; bare names map."""
    import transcribe
    monkeypatch.setattr(transcribe, "CACHE", tmp_path)
    (tmp_path / "ggml-medium.bin").write_bytes(b"x")
    (tmp_path / "ggml-custom.bin").write_bytes(b"x")
    assert transcribe._model_path("medium").endswith("ggml-medium.bin")
    assert transcribe._model_path("ggml-medium.bin").endswith("ggml-medium.bin")
    assert transcribe._model_path("ggml-custom.bin").endswith("ggml-custom.bin")
    assert transcribe._model_path("nonexistent") is None


def test_parse_lang_detection():
    """Issue #430: stderr detection lines -> (lang, prob)."""
    import transcribe
    assert transcribe.parse_lang_detection("") == (None, None)
    assert transcribe.parse_lang_detection(
        "whisper_full: detected language: Portuguese (p = 0.97)") == \
        ("portuguese", 0.97)
    assert transcribe.parse_lang_detection(
        "... lang pt (p = 0.42) ... lang en (p = 0.55)") == \
        ("en", 0.55)
    assert transcribe.parse_lang_detection("detected language: pt") == \
        ("pt", None)
