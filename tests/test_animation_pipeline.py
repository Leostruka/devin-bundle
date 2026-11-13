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
    plan = json.loads((wd / "src" / "plan.json").read_text(encoding="utf-8"))
    assert plan["beats"][0]["id"] == "b1"


# --- audit-r3: typed CLI errors ---------------------------------------------

def test_render_main_missing_plan_typed(tmp_path, capsys):
    code = render.main([str(tmp_path / "nope.json"),
                        "--workdir", str(tmp_path)])
    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and "unreadable" in out["error"]


# --- asr binary/model discovery ----------------------------------------------

def test_find_binary_prefers_release_dir(tmp_path, monkeypatch):
    rel = tmp_path / "Release"
    rel.mkdir()
    exe = rel / "whisper-cli.exe"
    exe.write_bytes(b"x")
    monkeypatch.setattr(transcribe, "CACHE", tmp_path)
    monkeypatch.setattr(transcribe.shutil, "which", lambda n: None)
    assert transcribe._find_binary() == str(exe)


def test_find_binary_never_which_main(tmp_path, monkeypatch):
    # a bare "main" on PATH (e.g. system32 main.CPL) must never win
    monkeypatch.setattr(transcribe, "CACHE", tmp_path)
    monkeypatch.setattr(
        transcribe.shutil, "which",
        lambda n: "C:/Windows/system32/main.CPL" if n == "main" else None)
    assert transcribe._find_binary() is None


def test_find_binary_which_namespaced_only(tmp_path, monkeypatch):
    monkeypatch.setattr(transcribe, "CACHE", tmp_path)
    monkeypatch.setattr(
        transcribe.shutil, "which",
        lambda n: "/usr/bin/whisper-cli" if n == "whisper-cli" else None)
    assert transcribe._find_binary() == "/usr/bin/whisper-cli"


def test_model_path_accepts_ggml_spelling(tmp_path):
    (tmp_path / "ggml-base.bin").write_bytes(b"x")
    import transcribe as t
    orig = t.CACHE
    try:
        t.CACHE = tmp_path
        assert t._model_path("base") == str(tmp_path / "ggml-base.bin")
        assert t._model_path("ggml-base") == str(tmp_path / "ggml-base.bin")
        assert t._model_path("ggml-base.bin") == \
            str(tmp_path / "ggml-base.bin")
        assert t._model_path("missing") is None
    finally:
        t.CACHE = orig


# --- plan_check CLI error contract (audit-r4 issue 01) -------------------------

def test_main_missing_file_typed_error(tmp_path, capsys):
    rc = plan_check.main([str(tmp_path / "nope.json")])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["errors"][0].startswith("read_error:")


def test_main_bad_json_typed_error(tmp_path, capsys):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    rc = plan_check.main([str(p)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["errors"][0].startswith("json_error:")


def test_main_non_dict_plan_typed_error(tmp_path, capsys):
    p = tmp_path / "arr.json"
    p.write_text("[1, 2]", encoding="utf-8")
    rc = plan_check.main([str(p)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert "plan must be a JSON object" in out["errors"][0]


def test_beats_non_list_typed_error():
    out = plan_check.check({"version": 2, "audio_duration_s": 10,
                            "beats": "x"})
    assert any("beats must be a list" in e for e in out["errors"])


def test_beat_non_dict_typed_error():
    p = _plan()
    p["beats"].append(42)
    out = plan_check.check(p)
    assert any("entry must be an object" in e for e in out["errors"])


def test_beat_visual_non_dict_typed_error():
    p = _plan()
    p["beats"][0]["visual"] = "kinetic"
    out = plan_check.check(p)
    assert any("visual must be an object" in e for e in out["errors"])


# --- composite.py (step 6: ffmpeg overlay) ---
import composite             # noqa: E402


def _info(w=1920, h=1080, audio=True, dur=10.0):
    streams = [{"codec_type": "video", "width": w, "height": h}]
    if audio:
        streams.append({"codec_type": "audio"})
    return {"streams": streams,
            "format": {"duration": str(dur)}}


def test_build_filter_frame_exact_dims():
    fc, label = composite.build_filter(1920, 1080, 640, 360, "frame")
    assert "scale=1920:1080" in fc
    assert "overlay=0:0" in fc
    assert label == "[v]"


def test_build_filter_contain_centers_with_offset():
    fc, _ = composite.build_filter(1920, 1080, 640, 360, "contain",
                                   (40, -20))
    assert "force_original_aspect_ratio=decrease" in fc
    assert "overlay=(W-w)/2+40:(H-h)/2+-20" in fc


def test_build_filter_bad_fit():
    import pytest
    with pytest.raises(ValueError):
        composite.build_filter(100, 100, 50, 50, "stretch")


def test_parse_pos_valid_and_invalid():
    assert composite._parse_pos("10:-5") == (10, -5)
    assert composite._parse_pos(None) == (0, 0)
    for bad in ("10", "a:b", "1:2:3", ""):
        import pytest
        with pytest.raises(ValueError):
            composite._parse_pos(bad)


def test_audio_mode_source_wins_without_mix():
    assert composite.audio_mode(_info(audio=True),
                                _info(audio=True)) == "source"
    assert composite.audio_mode(_info(audio=True),
                                _info(audio=True), mix=True) == "mix"
    assert composite.audio_mode(_info(audio=False),
                                _info(audio=True)) == "overlay"
    assert composite.audio_mode(_info(audio=False),
                                _info(audio=False)) == "none"


def _fake_probe(monkeypatch, src=None, ov=None):
    def fake(path, ffprobe=None):
        return ov if str(path).endswith(".mov") else src
    monkeypatch.setattr(composite, "probe", fake)


def test_composite_missing_input(tmp_path):
    out = composite.composite(tmp_path / "no.mp4", tmp_path / "o.mov",
                              tmp_path / "x.mp4", dry=True)
    assert out["ok"] is False and out["error"] == "source_missing"


def test_composite_dry_builds_cmd(tmp_path, monkeypatch):
    src, ov = tmp_path / "src.mp4", tmp_path / "ov.mov"
    src.write_bytes(b"x"); ov.write_bytes(b"x")
    _fake_probe(monkeypatch, src=_info(), ov=_info(w=640, h=360))
    out = composite.composite(src, ov, tmp_path / "x.mp4",
                              fit="contain", pos="10:20", dry=True)
    assert out["ok"] and out["note"] == "dry_run:cmd_built"
    joined = " ".join(out["cmd"])
    assert "overlay=(W-w)/2+10:(H-h)/2+20" in joined
    assert "-map" in out["cmd"] and "0:a:0" in out["cmd"]


def test_composite_pos_ignored_warning_on_frame_fit(tmp_path,
                                                    monkeypatch):
    src, ov = tmp_path / "s.mp4", tmp_path / "o.mov"
    src.write_bytes(b"x"); ov.write_bytes(b"x")
    _fake_probe(monkeypatch, src=_info(), ov=_info())
    out = composite.composite(src, ov, tmp_path / "x.mp4", pos="5:5",
                              dry=True)
    assert any("pos_ignored" in w for w in out["warnings"])


def test_composite_overlay_shorter_warns(tmp_path, monkeypatch):
    src, ov = tmp_path / "s.mp4", tmp_path / "o.mov"
    src.write_bytes(b"x"); ov.write_bytes(b"x")
    _fake_probe(monkeypatch, src=_info(dur=30.0),
                ov=_info(w=640, h=360, dur=10.0))
    out = composite.composite(src, ov, tmp_path / "x.mp4", dry=True)
    assert any("overlay_shorter" in w for w in out["warnings"])


def test_composite_mix_adds_amix_chain(tmp_path, monkeypatch):
    src, ov = tmp_path / "s.mp4", tmp_path / "o.mov"
    src.write_bytes(b"x"); ov.write_bytes(b"x")
    _fake_probe(monkeypatch, src=_info(), ov=_info(w=640, h=360))
    out = composite.composite(src, ov, tmp_path / "x.mp4", mix=True,
                              dry=True)
    fc = out["cmd"][out["cmd"].index("-filter_complex") + 1]
    assert "amix=inputs=2:duration=first" in fc
    assert "[a]" in out["cmd"]


def test_composite_ffmpeg_missing(tmp_path, monkeypatch):
    src, ov = tmp_path / "s.mp4", tmp_path / "o.mov"
    src.write_bytes(b"x"); ov.write_bytes(b"x")
    _fake_probe(monkeypatch, src=_info(), ov=_info())
    monkeypatch.setattr(composite, "find_ffmpeg", lambda: None)
    out = composite.composite(src, ov, tmp_path / "x.mp4", dry=False)
    assert out["ok"] is False and out["error"] == "ffmpeg_missing"


# --- transcribe.fetch_audio: video-container extraction (mp4 bug) ---

def test_fetch_audio_wav_passthrough(tmp_path):
    w = tmp_path / "a.wav"
    w.write_bytes(b"x")
    assert transcribe.fetch_audio(str(w), tmp_path) == w


def test_fetch_audio_mp4_uses_ffmpeg(tmp_path, monkeypatch):
    v = tmp_path / "narrated.mp4"
    v.write_bytes(b"x")
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        Path(cmd[-1]).write_bytes(b"wav")
        class R: returncode = 0
        return R()
    monkeypatch.setattr(transcribe.shutil, "which",
                        lambda n: "/ffmpeg" if n == "ffmpeg" else None)
    monkeypatch.setattr(transcribe.os, "environ", {})
    monkeypatch.setattr(transcribe.subprocess, "run", fake_run)
    out = transcribe.fetch_audio(str(v), tmp_path)
    assert out.name == "audio.wav" and out.exists()
    cmd = calls[0]
    assert cmd[0] == "/ffmpeg" and "-vn" in cmd and "-ar" in cmd
    assert "16000" in cmd


def test_fetch_audio_mp4_no_ffmpeg_errors(tmp_path, monkeypatch):
    v = tmp_path / "n.mp4"
    v.write_bytes(b"x")
    monkeypatch.setattr(transcribe.shutil, "which", lambda n: None)
    monkeypatch.setattr(transcribe.os, "environ", {})
    import pytest
    with pytest.raises(RuntimeError, match="ffmpeg"):
        transcribe.fetch_audio(str(v), tmp_path)


def test_fetch_audio_ffmpeg_exe_env(tmp_path, monkeypatch):
    v = tmp_path / "n.mkv"
    v.write_bytes(b"x")
    fake = tmp_path / "ffmpeg.exe"
    fake.write_bytes(b"x")
    monkeypatch.setattr(transcribe.os, "environ",
                        {"FFMPEG_EXE": str(fake)})
    monkeypatch.setattr(transcribe.shutil, "which", lambda n: None)
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        Path(cmd[-1]).write_bytes(b"wav")
        class R: returncode = 0
        return R()
    monkeypatch.setattr(transcribe.subprocess, "run", fake_run)
    out = transcribe.fetch_audio(str(v), tmp_path)
    assert calls[0][0] == str(fake) and out.exists()


# --- plan_check visual prop contract (counter crash regression) ---

def _plan_with_visual(vtype, props):
    p = _plan()
    p["beats"] = [{"id": "x", "sync_range": [0.5, 3.0],
                   "visual": {"type": vtype, "props": props}}]
    return p


def test_plan_check_counter_requires_numeric_to():
    out = plan_check.check(_plan_with_visual("counter", {"value": 1}))
    assert any("props.to missing" in e for e in out["errors"])
    out = plan_check.check(_plan_with_visual("counter", {"to": "5"}))
    assert any("props.to" in e for e in out["errors"])
    out = plan_check.check(_plan_with_visual("counter", {"to": True}))
    assert any("props.to" in e for e in out["errors"])


def test_plan_check_counter_valid():
    out = plan_check.check(_plan_with_visual("counter",
                                             {"to": 42, "label": "n"}))
    assert not [e for e in out["errors"] if "props" in e]


def test_plan_check_kinetic_text_requires_text():
    out = plan_check.check(_plan_with_visual("kinetic_text", {}))
    assert any("props.text" in e for e in out["errors"])


def test_plan_check_diagram_nodes_label_contract():
    out = plan_check.check(_plan_with_visual(
        "diagram_nodes", {"nodes": [{"label": "a"}, {"name": "b"}]}))
    assert any("nodes[1]" in e for e in out["errors"])


def test_plan_check_pan_zoom_requires_src():
    out = plan_check.check(_plan_with_visual("pan_zoom", {"zoom": 1.1}))
    assert any("props.src" in e for e in out["errors"])


def test_plan_check_unknown_visual_type_allowed():
    # template falls back to KineticText for unknown types - not an error
    out = plan_check.check(_plan_with_visual("hologram", {}))
    assert not [e for e in out["errors"] if "props" in e]


def test_fps_string_no_crash_typed_error():
    """fps:"30" must error, not TypeError inside check()."""
    p = _plan()
    p["fps"] = "30"
    out = plan_check.check(p)
    assert not out["ok"]
    assert any("fps" in e for e in out["errors"])


def test_nan_duration_and_props_rejected():
    p = _plan()
    p["audio_duration_s"] = float("nan")
    p["beats"][0]["visual"]["props"]["to"] = float("nan")
    out = plan_check.check(p)
    assert not out["ok"]
    assert any("audio_duration_s" in e for e in out["errors"])


def test_bool_sync_range_rejected():
    p = _plan()
    p["beats"][0]["sync_range"] = [False, True]
    out = plan_check.check(p)
    assert not out["ok"]
    assert any("sync_range" in e for e in out["errors"])


def test_composite_refuses_out_overwrite(tmp_path, monkeypatch):
    src, ov = tmp_path / "s.mp4", tmp_path / "o.mov"
    src.write_bytes(b"x"); ov.write_bytes(b"x")
    out = tmp_path / "x.mp4"
    out.write_bytes(b"old")
    _fake_probe(monkeypatch, src=_info(), ov=_info())
    res = composite.composite(src, ov, out, dry=True)
    assert res["ok"] is False and "out_exists" in res["error"]
    assert out.read_bytes() == b"old"


def test_composite_bad_fit_typed_error(tmp_path, monkeypatch):
    src, ov = tmp_path / "s.mp4", tmp_path / "o.mov"
    src.write_bytes(b"x"); ov.write_bytes(b"x")
    _fake_probe(monkeypatch, src=_info(), ov=_info())
    res = composite.composite(src, ov, tmp_path / "x.mp4", fit="bogus",
                              dry=True)
    assert res["ok"] is False and "fit" in res["error"]


def test_composite_main_exit_code_on_failure(tmp_path, monkeypatch,
                                             capsys):
    monkeypatch.setattr(sys, "argv",
                        ["composite.py", str(tmp_path / "no.mp4"),
                         str(tmp_path / "o.mov"),
                         "-o", str(tmp_path / "x.mp4")])
    rc = composite.main()
    assert rc == 1
    env = json.loads(capsys.readouterr().out)
    assert env["ok"] is False


def test_plan_check_main_exit_codes(tmp_path, capsys):
    """Invalid plan -> exit 1; valid -> 0 (gate must fail CI)."""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"version": 2,
                               "audio_duration_s": -5, "beats": []}), encoding="utf-8")
    rc = plan_check.main([str(bad)])
    assert rc == 1
    capsys.readouterr()
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_plan()), encoding="utf-8")
    rc = plan_check.main([str(good)])
    assert rc == 0


def test_transcribe_main_exit_code_on_failure(tmp_path, monkeypatch,
                                              capsys):
    monkeypatch.setattr(sys, "argv",
                        ["transcribe.py", str(tmp_path / "nope.wav")])
    rc = transcribe.main()
    assert rc == 1
    env = json.loads(capsys.readouterr().out)
    assert env["ok"] is False
