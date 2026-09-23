"""Gate for C07: pointer ops on the guest only — strict bounds against
current geometry, guest logical buttons, gestures as single cancelable
units, and an honest position query (no invented cache)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_qmp_backend = load("cu_qmp_backend")


def _evs(events):
    return [(e["type"], e["data"]) for e in events]


# --- strict axis bounds -----------------------------------------------------------

def test_out_of_frame_is_not_clamped():
    with pytest.raises(ValueError, match="out_of_bounds"):
        cu_qmp_backend.axis_to_qmp(1280, 1280)


def test_negative_axis_rejected():
    with pytest.raises(ValueError, match="out_of_bounds"):
        cu_qmp_backend.axis_to_qmp(-1, 1280)


def test_axis_edges_still_map():
    assert cu_qmp_backend.axis_to_qmp(0, 1280) == 0
    assert cu_qmp_backend.axis_to_qmp(1279, 1280) == 32767


# --- encoders ---------------------------------------------------------------------

def test_encode_move_absolute():
    ev = cu_qmp_backend.encode_move(640, 480, 1280, 960)
    kinds = [(e["type"], e["data"]["axis"]) for e in ev]
    assert kinds == [("abs", "x"), ("abs", "y")]
    assert ev[0]["data"]["value"] == \
        cu_qmp_backend.axis_to_qmp(640, 1280)


def test_encode_move_rejects_out_of_bounds():
    with pytest.raises(ValueError, match="out_of_bounds"):
        cu_qmp_backend.encode_move(1280, 0, 1280, 960)


def test_encode_click_move_then_button():
    ev = cu_qmp_backend.encode_click(10, 20, 1280, 960, "left")
    kinds = [e["type"] for e in ev]
    assert kinds == ["abs", "abs", "btn", "btn"]
    btn = [e for e in ev if e["type"] == "btn"]
    assert [(b["data"]["button"], b["data"]["down"])
            for b in btn] == [("left", True), ("left", False)]


def test_click_buttons_guest_logical():
    """Guest button names only — never host swap state."""
    for name, q in (("left", "left"), ("right", "right"),
                    ("middle", "middle")):
        ev = cu_qmp_backend.encode_click(1, 1, 10, 10, name)
        assert ev[2]["data"]["button"] == q
    with pytest.raises(cu_qmp_backend.UnsupportedText,
                       match="button"):
        cu_qmp_backend.encode_click(1, 1, 10, 10, "thumb")


def test_encode_scroll_wheel_notches():
    ev = cu_qmp_backend.encode_scroll(0, 2)  # +dy = down
    kinds = [(e["data"]["button"], e["data"]["down"])
             for e in ev]
    assert kinds == [("wheel-down", True), ("wheel-down", False),
                     ("wheel-down", True), ("wheel-down", False)]
    ev = cu_qmp_backend.encode_scroll(0, -1)
    assert ev[0]["data"]["button"] == "wheel-up"
    ev = cu_qmp_backend.encode_scroll(3, 0)
    assert ev[0]["data"]["button"] == "wheel-right"


def test_scroll_zero_is_empty():
    assert cu_qmp_backend.encode_scroll(0, 0) == []


def test_encode_drag_single_gesture():
    ev = cu_qmp_backend.encode_drag(0, 0, 99, 0, 100, 100)
    kinds = [e["type"] for e in ev]
    assert kinds[:3] == ["abs", "abs", "btn"]
    assert kinds[-1] == "btn" and ev[-1]["data"]["down"] is False
    moves = [e for e in ev if e["type"] == "abs"]
    assert len(moves) > 2  # interpolated path, not a teleport


def test_drag_path_stays_in_frame():
    ev = cu_qmp_backend.encode_drag(5, 5, 90, 90, 100, 100)
    xs = [e["data"]["value"] for e in ev
          if e["type"] == "abs" and e["data"]["axis"] == "x"]
    assert all(0 <= v <= 32767 for v in xs)


def test_drag_out_of_bounds_rejected_before_events():
    with pytest.raises(ValueError, match="out_of_bounds"):
        cu_qmp_backend.encode_drag(0, 0, 500, 500, 100, 100)


# --- backend pointer path ---------------------------------------------------------

@pytest.fixture
def env_dir(tmp_path):
    d = tmp_path / "devin-linux"
    d.mkdir()
    (d / "ready.json").write_text(json.dumps({
        "socket": "tcp://127.0.0.1:1", "token": "t0k",
        "qemu_pid": 1, "daemon_pid": 2}))
    return d


def test_pointer_dispatches_as_one_unit(env_dir):
    """A drag is ONE input-send-event call — cancelable as a unit,
    no half-gesture if the transport dies between chunks."""
    sent = []

    def ipc(sock, msg, timeout_s, token=None):
        sent.append(msg)
        return {"ok": True, "return": {}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    be.send_events(cu_qmp_backend.encode_drag(0, 0, 50, 50, 100, 100))
    assert len(sent) == 1


def test_lost_pointer_ack_releases_button(env_dir):
    calls = []

    def flaky(sock, msg, timeout_s, token=None):
        calls.append(msg)
        if len(calls) == 1:
            raise TimeoutError("ack lost")
        return {"ok": True, "return": {}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=flaky)
    with pytest.raises(cu_qmp_backend.BackendError, match="uncertain"):
        be.send_events(cu_qmp_backend.encode_click(1, 1, 10, 10,
                                                   "left"))
    ups = calls[1]["arguments"]["events"]
    assert any(e["type"] == "btn" and e["data"]["down"] is False
               for e in ups)


def test_position_query_is_honest(env_dir):
    """No real guest position source exists — reject instead of
    returning a last-command cache."""
    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=lambda *a, **k: {"ok": True,
                                                      "return": {}})
    with pytest.raises(cu_qmp_backend.BackendError,
                       match="position_unavailable"):
        be.pointer_position()


# --- mouse.py remote path ---------------------------------------------------------

def _write_env(tmp_path):
    reg = tmp_path / "envs"
    reg.mkdir()
    (reg / "devin-linux.json").write_text(json.dumps(
        {"env_id": "devin-linux", "provider": "qemu",
         "keyboard_layout": "en-us"}))


def test_mouse_remote_click_dispatches(tmp_path, monkeypatch, capsys):
    sent = []

    class FakeBackend:
        env_dir = tmp_path / "env"

        def send_events(self, events):
            sent.append(events)
            return {"dispatched": len(events)}

        def observe(self):
            return cu_qmp_backend.Frame(b"\x00" * 12, 2, 2), \
                {"backend": "qmp", "instance_id": "i-x"}

    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path / "envs"))
    cu_backend = load("cu_backend")
    monkeypatch.setattr(cu_backend, "open_backend",
                        lambda target: FakeBackend())
    mouse = load("mouse")
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "click", "1", "1",
                         "--env", "devin-linux"])
    mouse.main()
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is True and out["status"] == "dispatched"
    assert any(e["type"] == "btn" for e in sent[0])


def test_mouse_remote_click_out_of_bounds(tmp_path, monkeypatch, capsys):
    """Geometry validated against the CURRENT frame — a stale guess is
    not allowed to click into the void."""
    class FakeBackend:
        env_dir = tmp_path / "env"

        def observe(self):
            return cu_qmp_backend.Frame(b"\x00" * 12, 2, 2), \
                {"backend": "qmp", "instance_id": "i-x"}

        def send_events(self, events):  # must never run
            raise AssertionError("events sent for out-of-bounds click")

    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path / "envs"))
    cu_backend = load("cu_backend")
    monkeypatch.setattr(cu_backend, "open_backend",
                        lambda target: FakeBackend())
    mouse = load("mouse")
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "click", "500", "500",
                         "--env", "devin-linux"])
    with pytest.raises(SystemExit) as ei:
        mouse.main()
    assert ei.value.code != 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is False
    assert "out_of_bounds" in out["error"]


def test_mouse_remote_position_rejected(tmp_path, monkeypatch, capsys):
    class FakeBackend:
        env_dir = tmp_path / "env"

        def pointer_position(self):
            raise cu_qmp_backend.BackendError("position_unavailable")

        def observe(self):
            return cu_qmp_backend.Frame(b"\x00" * 12, 2, 2), \
                {"backend": "qmp", "instance_id": "i-x"}

    _write_env(tmp_path)
    monkeypatch.setenv("CU_ENV_ROOT", str(tmp_path / "envs"))
    cu_backend = load("cu_backend")
    monkeypatch.setattr(cu_backend, "open_backend",
                        lambda target: FakeBackend())
    mouse = load("mouse")
    monkeypatch.setattr(sys, "argv",
                        ["mouse.py", "position", "--env", "devin-linux"])
    with pytest.raises(SystemExit) as ei:
        mouse.main()
    assert ei.value.code != 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is False
    assert "position_unavailable" in out["error"]
