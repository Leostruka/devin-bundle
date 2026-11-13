"""screenshot.py gates: JSON-only stdout and the --no-image visual bypass."""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402


def test_no_image_bypass_json_contract(tmp_path):
    """--hints --no-image: JSON-only output, sidecar written, no PNG."""
    env = dict(os.environ, PYTHONPATH=str(cu_load.EXT),
               CU_HINT_TTL="120")
    r = subprocess.run(
        [sys.executable, str(cu_load.EXT / "screenshot.py"),
         "--hints", "--no-image", "--window", "all"],
        capture_output=True, text=True, env=env, timeout=60)
    out = json.loads(r.stdout)  # stdout is exactly one JSON object
    if out.get("ok") is False:
        pytest.skip("no UIA elements on this machine: %s" % out.get("error"))
    assert out["capture"] == "skipped" and out["path"] is None
    assert out["hints"] and "generation" in out and "session_id" in out


# -- --if-changed / --diff helpers ---------------------------------------------

shot = cu_load.load("screenshot")


class FakeImg:
    def __init__(self, rgb, w=10, h=10):
        self.rgb = rgb
        self.width = w
        self.height = h
        self.size = (w, h)


def test_img_hash_stable():
    a = FakeImg(b"\x00" * 300)
    assert shot._img_hash(a) == shot._img_hash(FakeImg(b"\x00" * 300))
    assert shot._img_hash(a) != shot._img_hash(FakeImg(b"\xff" * 300))


def test_shot_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(shot, "_STATE_PATH", str(tmp_path / "st.json"))
    assert shot._shot_state() == {}
    shot._write_shot_state("abc", "p.png")
    assert shot._shot_state() == {"sha256": "abc", "path": "p.png"}


def test_diff_file_ratios(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    base = tmp_path / "b.png"
    Image.new("RGB", (100, 100), (0, 0, 0)).save(base)
    img_a = FakeImg(bytes(100 * 100 * 3), 100, 100)  # all black = identical
    assert shot._diff_file(img_a, str(base)) == 0.0
    # 10x10 white block in corner = 1% of pixels changed
    px = bytearray(100 * 100 * 3)
    for y in range(10):
        for x in range(10):
            i = (y * 100 + x) * 3
            px[i:i + 3] = b"\xff\xff\xff"
    img_b = FakeImg(bytes(px), 100, 100)
    r = shot._diff_file(img_b, str(base))
    assert 0.008 < r < 0.012
    # size mismatch = everything changed
    img_c = FakeImg(bytes(50 * 50 * 3), 50, 50)
    assert shot._diff_file(img_c, str(base)) == 1.0
