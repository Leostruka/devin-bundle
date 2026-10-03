"""record.py gates: encoder selection honesty, sheet reservoir, pacing stats."""
import json
import os
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

rec = cu_load.load("record")


class FakeImg:
    def __init__(self, rgb, w=10, h=10):
        self.rgb = rgb
        self.width = w
        self.height = h
        self.size = (w, h)


# -- _pick_encoder -------------------------------------------------------------

def test_pick_encoder_explicit_ffmpeg_ext(monkeypatch, tmp_path):
    monkeypatch.setattr(rec.shutil, "which", lambda n: "/usr/bin/ffmpeg")
    assert rec._pick_encoder(str(tmp_path / "a.mp4")) == "ffmpeg"
    assert rec._pick_encoder(str(tmp_path / "a.webm")) == "ffmpeg"


def test_pick_encoder_ffmpeg_ext_without_ffmpeg(monkeypatch, tmp_path):
    """Explicit .mp4 with no ffmpeg on PATH is an honest exit-2, not a
    silent downgrade to Pillow."""
    monkeypatch.setattr(rec.shutil, "which", lambda n: None)
    with pytest.raises(SystemExit) as e:
        rec._pick_encoder(str(tmp_path / "a.mp4"))
    assert e.value.code == 2


def test_pick_encoder_pil_ext_never_needs_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr(rec.shutil, "which", lambda n: None)
    assert rec._pick_encoder(str(tmp_path / "a.webp")) == "pillow"
    assert rec._pick_encoder(str(tmp_path / "a.gif")) == "pillow"


def test_pick_encoder_default_prefers_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr(rec.shutil, "which", lambda n: "/x/ffmpeg")
    assert rec._pick_encoder(str(tmp_path / "a")) == "ffmpeg"
    monkeypatch.setattr(rec.shutil, "which", lambda n: None)
    assert rec._pick_encoder(str(tmp_path / "a")) == "pillow"


def test_pick_encoder_unknown_ext_rejects(monkeypatch, tmp_path):
    monkeypatch.setattr(rec.shutil, "which", lambda n: "/x/ffmpeg")
    with pytest.raises(SystemExit) as e:
        rec._pick_encoder(str(tmp_path / "a.avi"))
    assert e.value.code == 2


# -- _ffmpeg_cmd ---------------------------------------------------------------

def test_ffmpeg_cmd_streams_rgb24_and_pads_odd_dims(monkeypatch):
    monkeypatch.setattr(rec.shutil, "which", lambda n: "ffmpeg")
    cmd = rec._ffmpeg_cmd(101, 53, 8, "o.mp4")
    assert cmd[:2] == ["ffmpeg", "-y"]
    i = cmd.index("-s")
    assert cmd[i + 1] == "101x53"
    assert "scale=trunc(iw/2)*2:trunc(ih/2)*2" in cmd
    assert cmd[-1] == "o.mp4"
    assert "libx264" in cmd


def test_ffmpeg_cmd_webm_uses_vp9(monkeypatch):
    monkeypatch.setattr(rec.shutil, "which", lambda n: "ffmpeg")
    assert "libvpx-vp9" in rec._ffmpeg_cmd(64, 64, 8, "o.webm")


# -- _Sheet reservoir ----------------------------------------------------------

def test_sheet_caps_at_tiles_and_counts_seen(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    s = rec._Sheet(Image, tiles=4, cols=2)
    for i in range(50):
        s.feed(FakeImg(bytes([i % 256]) * 300, 10, 10))
    assert s.seen == 50
    assert len(s.thumbs) == 4  # reservoir bounded


def test_sheet_save_grid_geometry(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    s = rec._Sheet(Image, tiles=3, cols=2)
    for i in range(3):
        s.feed(FakeImg(bytes([i * 80]) * (200 * 100 * 3), 200, 100))
    out = str(tmp_path / "sheet.png")
    info = s.save(out)
    assert info["tiles"] == 3 and info["cols"] == 2
    with Image.open(out) as im:
        assert im.size == (200 * 2, 100 * 2)  # small frames never upscale


def test_sheet_save_empty_returns_none(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    s = rec._Sheet(Image, tiles=6, cols=3)
    assert s.save(str(tmp_path / "s.png")) is None


# -- _record pacing ------------------------------------------------------------

def test_record_pacing_counts_captured():
    """Every consumed frame is counted; slot count tolerates scheduler slack."""
    frame = FakeImg(b"\x00" * 300)
    calls = {"n": 0}

    def grab():
        calls["n"] += 1
        return frame, {}

    stats = {"captured": 0, "dropped": 0}
    rec._record(grab, seconds=0.25, fps=40,
                consume=lambda img: None, stats=stats)
    assert 5 <= stats["captured"] <= 12  # ~10 slots, jitter either way
    assert calls["n"] == stats["captured"]


def test_record_overrun_slots_counted_dropped():
    """A grab slower than the frame budget counts missed slots as dropped."""
    frame = FakeImg(b"\x00" * 300)

    def slow_grab():
        time.sleep(0.05)  # 2x the 25 ms slot at 40 fps
        return frame, {}

    stats = {"captured": 0, "dropped": 0}
    rec._record(slow_grab, seconds=0.2, fps=40,
                consume=lambda img: None, stats=stats)
    assert stats["dropped"] >= stats["captured"] - 1
    assert stats["captured"] >= 2


def test_record_stops_at_duration():
    frame = FakeImg(b"\x00" * 300)
    stats = {"captured": 0, "dropped": 0}
    t0 = time.monotonic()
    rec._record(lambda: (frame, {}), seconds=0.5, fps=10,
                consume=lambda img: None, stats=stats)
    assert time.monotonic() - t0 < 1.2
    assert stats["captured"] >= 2


# -- JSON contract (live capture, skips headless) ------------------------------

def test_cli_webp_contract(tmp_path):
    """End-to-end: animated webp + sheet, exactly one JSON object on stdout."""
    pytest.importorskip("PIL")
    out = tmp_path / "clip.webp"
    sheet = tmp_path / "sheet.png"
    env = dict(os.environ, PYTHONPATH=str(cu_load.EXT))
    r = subprocess.run(
        [sys.executable, str(cu_load.EXT / "record.py"),
         "--seconds", "0.4", "--fps", "5",
         "--out", str(out), "--sheet", str(sheet)],
        capture_output=True, text=True, env=env, timeout=120)
    res = json.loads(r.stdout)
    if res.get("ok") is False:
        pytest.skip("no display/capture backend: %s" % res.get("error"))
    assert res["encoder"] == "pillow"
    assert res["frames"] >= 2 and res["fps_actual"] > 0
    assert out.exists() and res["size_bytes"] > 0
    assert sheet.exists() and res["sheet"]["tiles"] >= 1
