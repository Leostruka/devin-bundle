"""stock-footage/fetch.py -- typed envelope + no-network-when-keyless."""
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

SF = Path(__file__).resolve().parents[1] / "extensions" / "stock-footage"
sys.path.insert(0, str(SF))

import fetch  # noqa: E402


def test_search_missing_key_pexels(monkeypatch, capsys):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with patch.object(fetch.urllib.request, "urlopen") as m:
        rc = fetch.main(["search", "--query", "ocean"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert out["ok"] is False and out["status"] == "missing"
    assert "PEXELS_API_KEY" in out["hint"]
    m.assert_not_called()


def test_search_missing_key_pixabay(monkeypatch, capsys):
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    with patch.object(fetch.urllib.request, "urlopen") as m:
        rc = fetch.main(["search", "--query", "x", "--provider", "pixabay"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["status"] == "missing"
    assert "PIXABAY_API_KEY" in out["hint"]
    m.assert_not_called()


def test_download_missing_key_no_network(monkeypatch, capsys):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with patch.object(fetch.urllib.request, "urlopen") as m:
        rc = fetch.main(["download", "--id", "1", "--out", "x.mp4"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["status"] == "missing"
    m.assert_not_called()


def test_pick_smallest_adequate():
    files = [{"width": 3840, "link": "u4k"},
             {"width": 1280, "link": "uhd"},
             {"width": 640, "link": "usd"}]
    assert fetch._pick(files, 720)["link"] == "uhd"
    assert fetch._pick(files, 4096)["link"] == "usd"


def test_search_http_error_typed(monkeypatch, capsys):
    monkeypatch.setenv("PEXELS_API_KEY", "k")

    def _boom(req, timeout=None):
        raise urllib.error.HTTPError("u", 429, "rate", {}, None)
    monkeypatch.setattr(fetch.urllib.request, "urlopen", _boom)
    rc = fetch.main(["search", "--query", "ocean"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert out["ok"] is False and out["status"] == "error"
    assert out["error"] == "http_error:429"


def test_search_pexels_ok(monkeypatch, capsys):
    monkeypatch.setenv("PEXELS_API_KEY", "k")
    payload = json.dumps({"videos": [{
        "id": 7, "width": 1080, "height": 1920, "duration": 12,
        "url": "https://pexels.com/v/7",
        "video_pictures": [{"picture": "p"}],
        "video_files": [{"quality": "hd", "width": 1080, "height": 1920,
                         "link": "https://f/7.mp4"}]}]}).encode()

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, n=-1):
            return payload

    monkeypatch.setattr(fetch.urllib.request, "urlopen",
                        lambda req, timeout=None: _Resp())
    rc = fetch.main(["search", "--query", "ocean",
                     "--orientation", "portrait"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"] is True
    hit = out["result"]["hits"][0]
    assert hit["id"] == 7 and hit["files"][0]["link"].endswith("7.mp4")
