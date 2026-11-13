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


def test_download_refuses_overwrite(monkeypatch, capsys, tmp_path):
    out_file = tmp_path / "clip.mp4"
    out_file.write_bytes(b"existing")
    monkeypatch.setenv("PEXELS_API_KEY", "k")
    video = {"id": 1, "width": 1920, "height": 1080,
             "video_files": [{"quality": "hd", "width": 1920,
                              "height": 1080, "link": "https://cdn/x.mp4"}]}

    class _Resp:
        def __init__(self, body): self.body = body
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n=-1): return self.body

    def fake_urlopen(req, timeout=None):
        if "videos/videos" in req.full_url:
            return _Resp(json.dumps(video).encode())
        return _Resp(b"filebytes")

    monkeypatch.setattr(fetch.urllib.request, "urlopen", fake_urlopen)
    rc = fetch.main(["download", "--id", "1",
                     "--out", str(out_file)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and "out_exists" in out["error"]
    assert out_file.read_bytes() == b"existing"


def test_search_non_dict_json_typed_error(monkeypatch, capsys):
    monkeypatch.setenv("PEXELS_API_KEY", "k")

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n=-1): return b"[1,2,3]"

    monkeypatch.setattr(fetch.urllib.request, "urlopen",
                        lambda req, timeout=None: _Resp())
    rc = fetch.main(["search", "--query", "x"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["status"] == "error"
    assert "not_an_object" in out["error"]


def _fake_hit():
    return {"id": 7, "width": 1920, "height": 1080, "duration": 12,
            "url": "https://x/v", "preview": "https://x/p.jpg",
            "files": [{"quality": "sd", "width": 640, "height": 360,
                       "link": "https://x/sd.mp4"},
                      {"quality": "hd", "width": 1920, "height": 1080,
                       "link": "https://x/hd.mp4"}]}


def test_shape_hits_full_unchanged():
    hits = [_fake_hit()]
    assert fetch._shape_hits(hits, "full") == hits


def test_shape_hits_brief_drops_files():
    out = fetch._shape_hits([_fake_hit()], "brief")
    assert out[0]["id"] == 7 and "files" not in out[0]
    assert out[0]["preview"] == "https://x/p.jpg"


def test_shape_hits_compact_keeps_best():
    out = fetch._shape_hits([_fake_hit()], "compact")
    assert out[0]["files_count"] == 2
    assert out[0]["best"]["link"] == "https://x/hd.mp4"
    assert "files" not in out[0]


def test_search_detail_flag_end_to_end(monkeypatch, capsys):
    monkeypatch.setenv("PEXELS_API_KEY", "k")
    payload = {"videos": [{"id": 7, "width": 1920, "height": 1080,
                           "duration": 12, "url": "https://x/v",
                           "video_pictures": [{"picture": "https://x/p"}],
                           "video_files": [
                               {"quality": "hd", "width": 1920,
                                "height": 1080, "link": "https://x/hd"}]}]}

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n=-1): return json.dumps(payload).encode()

    monkeypatch.setattr(fetch.urllib.request, "urlopen",
                        lambda req, timeout=None: _Resp())
    rc = fetch.main(["search", "--query", "x", "--detail", "brief"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["status"] == "ok"
    assert out["result"]["detail"] == "brief"
    assert "files" not in out["result"]["hits"][0]
