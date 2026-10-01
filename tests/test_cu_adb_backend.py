"""adb backend — fake `run` seam; encoders; registry/provider wiring."""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
cu_load.load("cu_target")
qmp = cu_load.load("cu_qmp_backend")
t = cu_load.load("cu_adb_backend")
cb = cu_load.load("cu_backend")

PPM = b"P6\n2 2\n255\n" + bytes([255, 0, 0] * 4)

UI_XML = b"""<?xml version="1.0"?>
<hierarchy><node index="0" text="" class="android.widget.FrameLayout"
 bounds="[0,0][1080,2400]" enabled="true">
 <node text="OK" class="android.widget.Button" clickable="true"
  bounds="[10,20][110,80]" enabled="true" content-desc="ok-btn"/>
 <node text="lbl" class="android.widget.TextView" clickable="false"
  bounds="[0,100][200,140]" enabled="true"/>
 <node text="hidden" class="android.widget.TextView" clickable="true"
  bounds="[0,0][0,0]" enabled="true"/>
</node></hierarchy>"""


def _proc(stdout=b"", stderr=b"", rc=0):
    return subprocess.CompletedProcess([], rc, stdout, stderr)


@pytest.fixture
def adb(tmp_path, monkeypatch):
    calls = []

    def run(argv, timeout_s):
        calls.append(list(argv))
        if argv[0] == "devices":
            return _proc(b"List of devices\nemu-1\tdevice\n")
        if "screencap" in argv:
            return _proc(b"\x89PNG fake marker")  # replaced below per test
        return _proc(b"ok\n")

    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    return calls, run


def _backend(run=None, serial="emu-1"):
    spec = {"serial": serial}
    return t.AdbBackend("phone", spec, run=run)


def test_serial_from_spec():
    b = _backend()
    assert b.serial() == "emu-1"
    assert "phone" in str(b.env_dir)


def test_serial_auto_resolve(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))

    def run(argv, tmo):
        return _proc(b"List of devices\nsolo-9\tdevice\n")
    b = t.AdbBackend("phone", {}, run=run)
    assert b.serial() == "solo-9"


def test_serial_ambiguous(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))

    def run(argv, tmo):
        return _proc(b"List of devices\na\tdevice\nb\tdevice\n")
    # serial resolves eagerly at construction (env_dir) — fail fast
    with pytest.raises(qmp.BackendError, match="ambiguous_devices"):
        t.AdbBackend("phone", {}, run=run)


def test_serial_none(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    with pytest.raises(qmp.BackendError, match="no_device"):
        t.AdbBackend("phone", {}, run=lambda a, t: _proc(b"List\n"))


def test_observe_decodes_frame(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    calls = []

    def run(argv, tmo):
        calls.append(argv)
        if "screencap" in argv:
            return _proc(PPM)   # magic-byte dispatch accepts P6
        return _proc()
    b = t.AdbBackend("phone", {"serial": "s1"}, run=run)
    img, meta = b.observe()
    assert (img.width, img.height) == (2, 2)
    assert meta["backend"] == "adb" and meta["instance_id"] == "s1"
    assert any(a[1] == "-s" or "exec-out" in a for a in calls)


def test_observe_rejects_non_image(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    b = t.AdbBackend("phone", {"serial": "s1"},
                     run=lambda a, t: _proc(b"not an image"))
    with pytest.raises(qmp.BackendError, match="unknown format"):
        b.observe()


def test_send_events_runs_shell(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    calls = []
    b = t.AdbBackend("phone", {"serial": "s1"},
                     run=lambda a, t: (calls.append(a), _proc())[1])
    r = b.send_events(t.encode_tap(5, 7) + t.encode_key("enter"))
    assert r["dispatched"] == 2
    assert calls[0][-4:] == ["input", "tap", 5, 7]
    assert calls[0][:3] == ["-s", "s1", "shell"]
    assert calls[1][-1] == 66  # KEYCODE_ENTER


def test_ui_elements_parses_tree(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))

    def run(argv, tmo):
        if "cat" in argv:
            return _proc(UI_XML)
        return _proc(b"UI hierchary dumped to: /data/local/tmp/cu-ui.xml\n")
    els = t.AdbBackend("phone", {"serial": "s1"}, run=run).ui_elements()
    ok = next(e for e in els if e["name"] == "OK")
    assert (ok["x"], ok["y"]) == (60, 50)
    assert ok["type"] == "Button"
    assert all(e["bounds"][2] > 0 and e["bounds"][3] > 0 for e in els)


def test_guest_exec_run(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path))
    calls = []
    b = t.AdbBackend("phone", {"serial": "s1"},
                     run=lambda a, t: (calls.append(a), _proc(b"hi\n"))[1])
    r = b.guest_call("exec.run", {"cmd": "echo hi"})
    assert r["stdout"] == "hi\n" and r["exit_code"] == 0
    assert calls[0][-2:] == ["-c", "echo hi"]
    assert "exec" in b.guest_caps()


def test_encoder_semantics():
    assert t.encode_tap(5, 7) == [["input", "tap", 5, 7]]
    assert t.encode_key("enter") == [["input", "keyevent", 66]]
    assert t.encode_text("a b%c")[0][-1] == "'a%sb%25c'"
    with pytest.raises(t.UnsupportedText):
        t.encode_text("héllo")
    with pytest.raises(t.UnsupportedOp):
        t.encode_chord("ctrl+c")
    with pytest.raises(t.UnsupportedOp):
        t.encode_move(1, 2, 100, 100)
    with pytest.raises(t.UnsupportedOp):
        t.encode_key("f24")
    sw = t.encode_drag(10, 20, 30, 40, 100, 200)
    assert sw[0][:2] == ["input", "swipe"] and sw[0][-1] >= 150


def test_open_backend_via_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path))
    monkeypatch.setenv("CU_STATE_ROOT", str(tmp_path / "state"))
    (tmp_path / "phone.json").write_text(
        '{"env_id": "phone", "provider": "adb", "serial": "s1"}')
    import cu_target
    tgt = cu_target.resolve_target("phone", cu_target.load_registry())
    b = cb.open_backend(tgt)
    assert isinstance(b, t.AdbBackend)
    assert b.serial() == "s1"
