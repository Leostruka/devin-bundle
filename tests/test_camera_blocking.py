"""camera-blocking contract tests — validation, clobber policy, exec flow
(mocked bpy transport), and playblast ingest with fake ffprobe. No real
Blender render is claimed here; real smoke evidence is produced
separately via camera_blocking.py CLI."""
import importlib.util
import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BO = ROOT / "extensions" / "blender-operator"
MT = ROOT / "extensions" / "media-tools"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cb = _load("camera_blocking", BO / "camera_blocking.py")
ingest = _load("playblast_ingest", MT / "playblast_ingest.py")


def _load_server():
    sys.modules.setdefault("bpy", types.SimpleNamespace(
        app=types.SimpleNamespace(version_string="4.3.0"),
        context=types.SimpleNamespace(scene=None),
        ops=types.SimpleNamespace(
            wm=types.SimpleNamespace(quit_blender=lambda: None))))
    return _load("blender_server_test", BO / "blender_server.py")


def test_server_rejects_non_dict_envelopes():
    srv = _load_server()
    for junk in ("[1,2]", '"str"', "42", "null", "true"):
        resp = srv._handle(json.loads(junk))
        assert resp["ok"] is False
        assert "object" in resp["error"]


def test_server_dict_envelope_still_works():
    srv = _load_server()
    resp = srv._handle({"op": "ping"})
    assert resp["ok"] is True and resp["blender"] == "4.3.0"


def _params(**over):
    p = {"out": "out", "name": "shot", "fps": 24, "frames": 48,
         "width": 640, "height": 360, "path": "orbit", "radius": 12.0,
         "cam_height": 5.0, "lens": 35.0, "engine": "BLENDER_WORKBENCH",
         "port": 19713, "exe": None, "force": False, "keep_server": False,
         "beats_per_second": 1}
    p.update(over)
    return p


def test_valid_params_pass():
    assert cb.validate_params(_params()) == []


@pytest.mark.parametrize("key,val", [
    ("fps", 0), ("fps", 121), ("frames", 1), ("frames", 481),
    ("width", 8), ("height", 5000), ("radius", 0.0),
    ("cam_height", 0.0), ("lens", 0.5), ("lens", 400.0),
    ("port", 80), ("port", 70000)])
def test_numeric_limits_rejected(key, val):
    bad = cb.validate_params(_params(**{key: val}))
    assert bad and key in bad[0]


@pytest.mark.parametrize("name", ["", "../x", "a/b", "a b", "x" * 65, "a;b"])
def test_bad_names_rejected(name):
    bad = cb.validate_params(_params(name=name))
    assert bad and "name" in bad[0]


def test_bad_path_and_engine_rejected():
    assert cb.validate_params(_params(path="spiral"))
    assert cb.validate_params(_params(engine="CYCLES"))


def test_missing_out_rejected():
    assert cb.validate_params(_params(out=""))


def test_clobber_refused(tmp_path):
    (tmp_path / "shot.mp4").write_bytes(b"x")
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"] is False
    assert r["stage"] == "clobber"
    assert "shot.mp4" in r["errors"][0]


def test_clobber_each_artifact(tmp_path):
    for f in ("shot.camera.json", "shot.preview.png", "shot.handoff.json"):
        (tmp_path / f).write_text("{}")
        r = cb.run(_params(out=str(tmp_path)))
        assert r["stage"] == "clobber"
        (tmp_path / f).unlink()


def test_force_allows_past_clobber(tmp_path, monkeypatch):
    (tmp_path / "shot.mp4").write_bytes(b"x")
    monkeypatch.setattr(cb.wrapper, "find_blender", lambda e: None)
    r = cb.run(_params(out=str(tmp_path), force=True))
    assert r["stage"] == "launch"
    assert "blender" in r["errors"][0]


def _fake_run_env(monkeypatch, tmp_path, preset_results=None):
    """Mock blender + transport; capture exec payloads."""
    sent = []
    monkeypatch.setattr(cb.wrapper, "find_blender", lambda e: "/bin/blender")

    class P:
        pid = 4242

        def poll(self):
            return None

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    monkeypatch.setattr(cb.subprocess, "Popen", lambda *a, **k: P())

    calls = {"n": 0}

    def fake_alive(port):
        calls["n"] += 1
        return (calls["n"] > 1, {"blender": "test"})

    monkeypatch.setattr(cb.wrapper, "_alive", fake_alive)

    def fake_request(port, payload, timeout=30):
        sent.append(payload)
        base = {"ok": True, "pid": 4242, "nonce": "n1"}
        if payload["op"] == "ping":
            return base
        if payload["op"] == "shutdown":
            return base
        for preset, resp in (preset_results or {}).items():
            if preset in payload.get("code", ""):
                out = dict(base)
                out.update(resp)
                return out
        return dict(base, result_json="{}")

    monkeypatch.setattr(cb.wrapper, "_request", fake_request)
    monkeypatch.setattr(cb.ingest, "ingest_playblast",
                        lambda *a, **k: {"video": {"fps": 24},
                                         "prompt_template": {"beats": [1]}})
    return sent


def test_run_executes_presets_in_order(monkeypatch, tmp_path):
    sent = _fake_run_env(monkeypatch, tmp_path)
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"], r
    codes = [p.get("code", "") for p in sent if p["op"] == "exec"]
    assert len(codes) == 3
    assert codes[0].index("blockout.py") >= 0
    assert codes[1].index("camera_rig.py") >= 0
    assert codes[2].index("playblast.py") >= 0
    assert "PARAMS" in codes[0]
    assert any(p["op"] == "shutdown" for p in sent)


def test_run_aborts_on_preset_error(monkeypatch, tmp_path):
    sent = _fake_run_env(monkeypatch, tmp_path, preset_results={
        "camera_rig.py": {"ok": False, "error": "boom"}})
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"] is False
    assert r["stage"] == "camera_rig.py"
    codes = [p.get("code", "") for p in sent if p["op"] == "exec"]
    assert not any("playblast.py" in c for c in codes)


def test_run_uses_factory_startup_no_blend(monkeypatch, tmp_path):
    popen_argv = []

    class P:
        pid = 1

        def poll(self):
            return None

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    def fake_popen(argv, **kw):
        popen_argv.extend(argv)
        return P()

    monkeypatch.setattr(cb.wrapper, "find_blender", lambda e: "/bin/blender")
    monkeypatch.setattr(cb.subprocess, "Popen", fake_popen)
    calls = {"n": 0}

    def fake_alive(port):
        calls["n"] += 1
        return (calls["n"] > 1, {"blender": "test"})

    monkeypatch.setattr(cb.wrapper, "_alive", fake_alive)
    monkeypatch.setattr(cb.wrapper, "_request",
                        lambda port, pl, timeout=30:
                        {"ok": True, "result_json": None,
                         "pid": 1, "nonce": "n"})
    monkeypatch.setattr(cb.ingest, "ingest_playblast",
                        lambda *a, **k: {"video": {},
                                         "prompt_template": {"beats": []}})
    cb.run(_params(out=str(tmp_path)))
    assert "--factory-startup" in popen_argv
    assert ".blend" not in " ".join(popen_argv)
    assert "blender_server.py" in " ".join(popen_argv)


def test_port_in_use_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(cb.wrapper, "find_blender", lambda e: "/bin/blender")
    monkeypatch.setattr(cb.wrapper, "_alive",
                        lambda port: (True, {"blender": "x"}))
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"] is False and "port" in r["errors"][0]


@pytest.mark.parametrize("f", ["blockout.py", "camera_rig.py",
                               "playblast.py"])
def test_preset_compiles(f):
    src = (BO / "presets" / f).read_text()
    compile(src, f, "exec")


def test_presets_do_not_wipe_scene():
    for f in ("blockout.py", "camera_rig.py", "playblast.py"):
        src = (BO / "presets" / f).read_text()
        assert "read_homefile" not in src
        assert "bpy.ops.wm.open_mainfile" not in src
        assert "object.delete" not in src


def _camera_meta(fps=24, f0=1, f1=48, w=640, h=360):
    frames = [{"frame": f,
               "matrix_world": [[1 if i == j else 0 for j in range(4)]
                                for i in range(4)],
               "location": [0.0, 0.0, 5.0],
               "rotation_euler": [0.0, 0.0, 0.0],
               "lens": 35.0} for f in range(f0, f1 + 1)]
    return {"fps": fps, "frame_start": f0, "frame_end": f1,
            "camera": "CAM", "width": w, "height": h, "frames": frames}


def _ffprobe_json(fps="24/1", n=48, w=640, h=360, dur=2.0):
    return {"streams": [{"codec_type": "video", "codec_name": "h264",
                         "width": w, "height": h, "avg_frame_rate": fps,
                         "r_frame_rate": fps, "nb_frames": str(n),
                         "duration": str(dur)}],
            "format": {"duration": str(dur)}}


def _fake_ffprobe(payload):
    def fake(exe_args, capture_output, text, timeout):
        class R:
            returncode = 0
            stdout = json.dumps(payload)
            stderr = ""
        return R()
    return fake


def test_ingest_happy_path(tmp_path, monkeypatch):
    mp4 = tmp_path / "shot.mp4"
    mp4.write_bytes(b"fake-mp4")
    cam = tmp_path / "shot.camera.json"
    cam.write_text(json.dumps(_camera_meta()))
    monkeypatch.setattr(ingest.subprocess, "run",
                        _fake_ffprobe(_ffprobe_json()))
    monkeypatch.setattr(ingest, "find_ffprobe", lambda: "/bin/ffprobe")
    desc = ingest.ingest_playblast(str(mp4))
    assert desc["kind"] == "camera-blocking-handoff"
    assert desc["target"]["external_call"] is False
    assert desc["video"]["fps"] == 24
    assert len(desc["prompt_template"]["beats"]) >= 2
    assert (tmp_path / "shot.handoff.json").exists()


def test_ingest_fps_mismatch(tmp_path, monkeypatch):
    mp4 = tmp_path / "s.mp4"
    mp4.write_bytes(b"x")
    (tmp_path / "s.camera.json").write_text(
        json.dumps(_camera_meta(fps=24)))
    monkeypatch.setattr(ingest.subprocess, "run",
                        _fake_ffprobe(_ffprobe_json(fps="30/1", n=60)))
    monkeypatch.setattr(ingest, "find_ffprobe", lambda: "/bin/ffprobe")
    with pytest.raises(ValueError, match="fps"):
        ingest.ingest_playblast(str(mp4))


def test_ingest_framecount_mismatch(tmp_path, monkeypatch):
    mp4 = tmp_path / "s.mp4"
    mp4.write_bytes(b"x")
    (tmp_path / "s.camera.json").write_text(json.dumps(_camera_meta()))
    monkeypatch.setattr(ingest.subprocess, "run",
                        _fake_ffprobe(_ffprobe_json(n=200)))
    monkeypatch.setattr(ingest, "find_ffprobe", lambda: "/bin/ffprobe")
    with pytest.raises(ValueError, match="frame count"):
        ingest.ingest_playblast(str(mp4))


def test_ingest_camera_schema_enforced(tmp_path):
    bad = tmp_path / "bad.camera.json"
    bad.write_text(json.dumps({"fps": 24, "frames": []}))
    with pytest.raises(ValueError, match="missing"):
        ingest.load_camera(str(bad))


def test_ingest_ffprobe_timeout_typed(tmp_path, monkeypatch):
    mp4 = tmp_path / "s.mp4"
    mp4.write_bytes(b"x")
    (tmp_path / "s.camera.json").write_text(json.dumps(_camera_meta()))

    def hang(*a, **k):
        raise ingest.subprocess.TimeoutExpired("ffprobe", 60)
    monkeypatch.setattr(ingest.subprocess, "run", hang)
    monkeypatch.setattr(ingest, "find_ffprobe", lambda: "/bin/ffprobe")
    with pytest.raises(ValueError, match="timed out"):
        ingest.ingest_playblast(str(mp4))


def test_memory_retrieval_skips_unreadable_note(tmp_path):
    mem = tmp_path / "mem"
    mem.mkdir()
    (mem / "good.md").write_text(
        "---\ntitle: T\ncategory: ops\nstatus: active\n"
        "  - keyword: compaction\n---\nbody line one\n",
        encoding="utf-8")
    (mem / "bad.md").write_bytes(b"\xff\xfe\x00bad")
    env = dict(os.environ, BUNDLE_MEMORY_DIR=str(mem))
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "memory-retrieval.py")],
        input=json.dumps({"hook_event_name": "UserPromptSubmit",
                          "prompt": "compaction please"}),
        capture_output=True, text=True, env=env, timeout=30)
    assert p.returncode == 0
    assert "additionalContext" in p.stdout
    assert "skipping unreadable note" in p.stderr


def test_ingest_missing_mp4(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest.ingest_playblast(str(tmp_path / "nope.mp4"))


def test_ingest_no_clobber(tmp_path, monkeypatch):
    mp4 = tmp_path / "s.mp4"
    mp4.write_bytes(b"x")
    (tmp_path / "s.camera.json").write_text(json.dumps(_camera_meta()))
    (tmp_path / "s.handoff.json").write_text("{}")
    monkeypatch.setattr(ingest.subprocess, "run",
                        _fake_ffprobe(_ffprobe_json()))
    monkeypatch.setattr(ingest, "find_ffprobe", lambda: "/bin/ffprobe")
    with pytest.raises(FileExistsError):
        ingest.ingest_playblast(str(mp4))


class _FakeProc:
    def __init__(self, pid=4242):
        self.pid = pid
        self.killed = False

    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


def _ownership_env(monkeypatch, tmp_path, proc, responder):
    sent = []
    monkeypatch.setattr(cb.wrapper, "find_blender", lambda e: "/bin/blender")
    monkeypatch.setattr(cb.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(cb.wrapper, "_alive", lambda port: (False, {}))

    def fake_request(port, payload, timeout=30):
        sent.append(payload)
        return responder(payload, len(sent))

    monkeypatch.setattr(cb.wrapper, "_request", fake_request)
    monkeypatch.setattr(cb.ingest, "ingest_playblast",
                        lambda *a, **k: {"video": {},
                                         "prompt_template": {"beats": []}})
    return sent


def test_foreign_pid_at_launch_no_exec(monkeypatch, tmp_path):
    proc = _FakeProc()
    sent = _ownership_env(
        monkeypatch, tmp_path, proc,
        lambda pl, n: {"ok": True, "pid": 9999, "nonce": "foreign"})
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"] is False and r["stage"] == "launch"
    assert "foreign" in r["errors"][0] or "not our spawned" in r["errors"][0]
    ops = [p["op"] for p in sent]
    assert "exec" not in ops and "shutdown" not in ops


def test_pid_swap_mid_run_aborts(monkeypatch, tmp_path):
    proc = _FakeProc()
    state = {"swapped": False}

    def responder(pl, n):
        if pl["op"] == "exec" and "camera_rig.py" in pl.get("code", ""):
            state["swapped"] = True
        if state["swapped"]:
            return {"ok": True, "pid": 7777, "nonce": "other"}
        return {"ok": True, "pid": proc.pid, "nonce": "n1",
                "result_json": "{}"}

    sent = _ownership_env(monkeypatch, tmp_path, proc, responder)
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"] is False
    assert "ownership" in r["errors"][0] or "foreign" in r["errors"][0]
    execs = [p for p in sent if p["op"] == "exec"]
    assert state["swapped"] and len(execs) == 2
    assert not any("playblast.py" in p.get("code", "") for p in execs)
    assert not any(p["op"] == "shutdown" for p in sent
                   if state["swapped"])


def test_exec_and_shutdown_carry_nonce(monkeypatch, tmp_path):
    proc = _FakeProc()
    sent = _ownership_env(
        monkeypatch, tmp_path, proc,
        lambda pl, n: {"ok": True, "pid": proc.pid, "nonce": "n1",
                       "result_json": "{}"})
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"], r
    for p in sent:
        if p["op"] in ("exec", "shutdown"):
            assert p.get("nonce") == "n1"


def test_responder_without_identity_rejected(monkeypatch, tmp_path):
    proc = _FakeProc()
    sent = _ownership_env(monkeypatch, tmp_path, proc,
                          lambda pl, n: {"ok": True})
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"] is False and r["stage"] == "launch"
    assert not any(p["op"] == "exec" for p in sent)


@pytest.mark.parametrize("key,val", [
    ("fps", "24"), ("fps", True), ("fps", float("nan")),
    ("fps", float("inf")), ("fps", None), ("frames", "48"),
    ("width", None), ("radius", "big"), ("lens", False),
    ("port", "19713"), ("beats_per_second", float("nan"))])
def test_wrong_type_params_typed_errors(key, val):
    p = _params()
    p.pop(key, None)
    p[key] = val
    bad = cb.validate_params(p)
    assert bad and any(key in b for b in bad)


def test_validate_params_missing_required():
    p = _params()
    for k in ("fps", "frames", "name", "out"):
        p.pop(k)
    bad = cb.validate_params(p)
    assert any("fps" in b for b in bad)
    assert any("frames" in b for b in bad)
    assert any("name" in b for b in bad)
    assert any("out" in b for b in bad)


def test_validate_params_non_dict():
    assert cb.validate_params("nope") == ["params must be a dict"]


def test_run_never_raises_on_junk(tmp_path):
    r = cb.run({"out": str(tmp_path), "name": None, "fps": "x"})
    assert r["ok"] is False and r["stage"] == "validate"


def test_ingest_rejects_nonfinite(tmp_path):
    import math
    for bad_val in (float("nan"), float("inf")):
        meta = _camera_meta()
        meta["frames"][0]["location"] = [bad_val, 0.0, 0.0]
        f = tmp_path / "c.json"
        f.write_text(json.dumps(meta))
        with pytest.raises(ValueError, match="non-finite"):
            ingest.load_camera(str(f))


def test_ingest_rejects_bad_frame_types(tmp_path):
    meta = _camera_meta()
    meta["frames"][0]["location"] = "here"
    f = tmp_path / "c.json"
    f.write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="3-vec"):
        ingest.load_camera(str(f))
    meta = _camera_meta()
    meta["fps"] = float("inf")
    f.write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="fps"):
        ingest.load_camera(str(f))


def _write_cam(tmp_path, meta):
    f = tmp_path / "c.json"
    f.write_text(json.dumps(meta))
    return str(f)


def test_camera_gap_duplicate_unordered_rejected(tmp_path):
    meta = _camera_meta(f1=4)
    del meta["frames"][2]
    with pytest.raises(ValueError, match="cover|expected"):
        ingest.load_camera(_write_cam(tmp_path, meta))
    meta = _camera_meta(f1=4)
    meta["frames"].insert(1, dict(meta["frames"][1]))
    with pytest.raises(ValueError):
        ingest.load_camera(_write_cam(tmp_path, meta))
    meta = _camera_meta(f1=4)
    meta["frames"][0], meta["frames"][1] = \
        meta["frames"][1], meta["frames"][0]
    with pytest.raises(ValueError, match="order|expected"):
        ingest.load_camera(_write_cam(tmp_path, meta))
    meta = _camera_meta(f1=4)
    meta["frames"][0]["frame"] = 1.5
    with pytest.raises(ValueError, match="int"):
        ingest.load_camera(_write_cam(tmp_path, meta))
    meta = _camera_meta(f1=4)
    meta["frames"] = meta["frames"][:-1]
    with pytest.raises(ValueError, match="cover"):
        ingest.load_camera(_write_cam(tmp_path, meta))


def test_camera_span_and_size_bounds(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, "MAX_FRAMES", 10)
    meta = _camera_meta(f1=100)
    with pytest.raises(ValueError, match="span"):
        ingest.load_camera(_write_cam(tmp_path, meta))
    monkeypatch.setattr(ingest, "MAX_FRAMES", 200000)
    monkeypatch.setattr(ingest, "MAX_META_BYTES", 100)
    with pytest.raises(ValueError, match="too large"):
        ingest.load_camera(_write_cam(tmp_path, meta))


def test_camera_exact_coverage_accepted(tmp_path):
    meta = _camera_meta(f0=7, f1=10)
    got = ingest.load_camera(_write_cam(tmp_path, meta))
    assert [f["frame"] for f in got["frames"]] == [7, 8, 9, 10]


def test_beats_fractional_per_second():
    meta = _camera_meta(fps=24, f0=1, f1=48)
    beats = ingest._beats(meta, 0.5)
    assert [b["frame"] for b in beats] == [1, 48]
    beats = ingest._beats(meta, 2)
    ts = [b["t"] for b in beats]
    assert ts[0] == 0.0 and ts[-1] == round(47 / 24, 3)
    assert len(beats) == len({b["frame"] for b in beats})
    meta25 = _camera_meta(fps=24, f0=1, f1=25)
    beats = ingest._beats(meta25, 1)
    assert beats[-1]["frame"] == 25
    assert len(beats) == len({b["frame"] for b in beats})


def test_beats_per_second_out_of_range(tmp_path, monkeypatch):
    mp4 = tmp_path / "s.mp4"
    mp4.write_bytes(b"x")
    (tmp_path / "s.camera.json").write_text(json.dumps(_camera_meta()))
    monkeypatch.setattr(ingest.subprocess, "run",
                        _fake_ffprobe(_ffprobe_json()))
    monkeypatch.setattr(ingest, "find_ffprobe", lambda: "/bin/ffprobe")
    for bad in (0, -1, float("nan"), 61, "fast"):
        with pytest.raises((ValueError, TypeError)):
            ingest.ingest_playblast(str(mp4), beats_per_second=bad)


def test_run_without_optional_flags(tmp_path, monkeypatch):
    monkeypatch.setattr(cb.wrapper, "find_blender", lambda e: None)
    p = _params(out=str(tmp_path))
    for k in ("force", "keep_server", "exe", "beats_per_second"):
        p.pop(k, None)
    r = cb.run(p)
    assert r["ok"] is False and r["stage"] == "launch"


def test_run_ingest_oserror_structured(tmp_path, monkeypatch):
    _fake_run_env(monkeypatch, tmp_path)
    monkeypatch.setattr(cb.ingest, "ingest_playblast",
                        lambda *a, **k: (_ for _ in ()).throw(
                            FileExistsError("exists")))
    r = cb.run(_params(out=str(tmp_path)))
    assert r["ok"] is False and r["stage"] == "ingest"
    assert "exists" in r["errors"][0]


def test_ingest_cli_structured_error(tmp_path, monkeypatch, capsys):
    mp4 = tmp_path / "s.mp4"
    mp4.write_bytes(b"x")
    (tmp_path / "s.camera.json").write_text(json.dumps(_camera_meta()))
    (tmp_path / "s.handoff.json").write_text("{}")
    monkeypatch.setattr(ingest.subprocess, "run",
                        _fake_ffprobe(_ffprobe_json()))
    monkeypatch.setattr(ingest, "find_ffprobe", lambda: "/bin/ffprobe")
    rc = ingest.main([str(mp4)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["ok"] is False
    assert "overwrite" in out["error"]
