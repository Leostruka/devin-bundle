"""animation-direction — ASR parsing, plan_check validator, render dry-run."""
import json
import sys
from pathlib import Path

ASR = Path(__file__).resolve().parents[1] / "extensions" / "asr"
RR = Path(__file__).resolve().parents[1] / "extensions" / "remotion-render"
sys.path.insert(0, str(ASR))
sys.path.insert(0, str(RR))

import transcribe               # noqa: E402
import plan_check               # noqa: E402
import render                   # noqa: E402

WHISPER_OUT = """
whisper_init_from_file_no_state: loading model
[00:00:01.200 --> 00:00:04.800]   Oi, hoje eu vou explicar filas
[00:00:04.800 --> 00:00:09.000]   uma fila de pedidos funciona assim
[00:00:09.100 --> 00:00:12.000]   e aqui entra a animacao
"""


def _plan(**kw):
    base = {"version": 2, "audio_duration_s": 12.0, "fps": 30,
            "size": [1920, 1080],
            "beats": [
                {"id": "b1", "sync_range": [1.0, 5.0],
                 "visual": {"type": "kinetic_text",
                            "props": {"text": "filas de pedidos"}},
                 "motion_spec": {"enter": "slideUp", "enter_s": 0.4}},
                {"id": "b2", "sync_range": [5.0, 9.0],
                 "visual": {"type": "diagram_nodes",
                            "props": {"nodes": [{"label": "pedido"},
                                                {"label": "cozinha"}]}},
                 "motion_spec": {"enter": "fade"}},
            ]}
    base.update(kw)
    return base


# --- ASR ---------------------------------------------------------------------

def test_parse_segments_timestamps_and_text():
    segs = transcribe.parse_segments(WHISPER_OUT)
    assert len(segs) == 3
    assert abs(segs[0]["start"] - 1.2) < 0.001
    assert abs(segs[0]["end"] - 4.8) < 0.001
    assert "filas" in segs[0]["text"]


def test_transcribe_missing_binary_abstains(tmp_path, monkeypatch):
    monkeypatch.setenv("ASR_CACHE", str(tmp_path))
    monkeypatch.setattr(transcribe, "CACHE", tmp_path)
    monkeypatch.setattr(transcribe.shutil, "which", lambda n: None)
    out = transcribe.transcribe("file.wav")
    assert out["ok"] is False
    assert out["error"] in ("whisper_binary_missing", "yt-dlp_missing")


# --- plan_check ----------------------------------------------------------------

def test_valid_plan_passes():
    out = plan_check.check(_plan())
    assert out["ok"], out["errors"]
    assert out["budget"]["frames"] > 0


def test_overlap_detected():
    p = _plan()
    p["beats"][1]["sync_range"] = [4.5, 9.0]
    out = plan_check.check(p)
    assert not out["ok"]
    assert any("overlaps" in e for e in out["errors"])


def test_beat_beyond_audio_errors():
    p = _plan()
    p["beats"][0]["sync_range"] = [1.0, 20.0]
    out = plan_check.check(p)
    assert any("beyond audio" in e for e in out["errors"])


def test_read_time_warning():
    p = _plan()
    p["beats"][0]["sync_range"] = [1.0, 1.5]
    p["beats"][0]["visual"]["props"]["text"] = " ".join(["word"] * 20)
    out = plan_check.check(p)
    assert any("read time" in w for w in out["warnings"])


def test_overlay_beat_allowed():
    p = _plan()
    p["beats"].append({"id": "b3", "sync_range": [4.5, 8.0],
                       "overlay": True,
                       "visual": {"type": "counter",
                                  "props": {"to": 42}}})
    out = plan_check.check(p)
    assert out["ok"], out["errors"]


# --- render materialization ------------------------------------------------------

def test_render_dry_materializes_project(tmp_path):
    out = render.render(_plan(), tmp_path / "proj", dry=True)
    assert out["ok"] and not out["rendered"]
    wd = Path(out["workdir"])
    assert (wd / "src" / "plan.json").exists()
    assert (wd / "package.json").exists()
    plan = json.loads((wd / "src" / "plan.json").read_text())
    assert plan["beats"][0]["id"] == "b1"
