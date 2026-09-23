"""Gate for C06: keyboard input to the guest only — encode_text /
encode_key / encode_chord pure encoders, send_events chunking, modifier
balancing, and zero host input anywhere on the remote path.
"""
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_qmp_backend = load("cu_qmp_backend")


def _codes(events):
    return [(e["data"]["key"]["data"], e["data"]["down"])
            for e in events]


# --- encode_text -----------------------------------------------------------------

def test_plain_ascii_down_up():
    ev = cu_qmp_backend.encode_text("ab", layout="en-us")
    assert _codes(ev) == [("a", True), ("a", False),
                          ("b", True), ("b", False)]


def test_uppercase_wraps_shift_chord():
    ev = cu_qmp_backend.encode_text("A", layout="en-us")
    assert _codes(ev) == [("shift", True), ("a", True),
                          ("a", False), ("shift", False)]


def test_shifted_symbol_uses_shift():
    ev = cu_qmp_backend.encode_text("!", layout="en-us")
    assert _codes(ev) == [("shift", True), ("1", True),
                          ("1", False), ("shift", False)]


def test_newline_and_tab_map_to_ret_tab():
    codes = _codes(cu_qmp_backend.encode_text("x\ny\t", layout="en-us"))
    assert ("ret", True) in codes and ("tab", True) in codes


def test_unsupported_text_never_sends_prefix():
    with pytest.raises(cu_qmp_backend.UnsupportedText):
        cu_qmp_backend.encode_text("abc漢字", layout="en-us")


def test_control_char_rejected():
    with pytest.raises(cu_qmp_backend.UnsupportedText):
        cu_qmp_backend.encode_text("a\x01b", layout="en-us")


def test_unknown_layout_rejected():
    with pytest.raises(cu_qmp_backend.UnsupportedText, match="layout"):
        cu_qmp_backend.encode_text("a", layout="klingon")


def test_every_down_has_matching_up():
    for text in ("Hello, World! 123", "aA!@#$%^&*()"):
        ev = cu_qmp_backend.encode_text(text, layout="en-us")
        downs = [c for c, d in _codes(ev) if d]
        ups = [c for c, d in _codes(ev) if not d]
        assert sorted(downs) == sorted(ups)


# --- encode_key / encode_chord ----------------------------------------------------

def test_named_key():
    assert _codes(cu_qmp_backend.encode_key("enter")) == \
        [("ret", True), ("ret", False)]


def test_unknown_named_key_rejected():
    with pytest.raises(cu_qmp_backend.UnsupportedText):
        cu_qmp_backend.encode_key("notakey")


def test_chord_modifiers_release_in_reverse_order():
    ev = cu_qmp_backend.encode_chord("ctrl+alt+delete")
    assert _codes(ev) == [
        ("ctrl", True), ("alt", True),
        ("delete", True), ("delete", False),
        ("alt", False), ("ctrl", False)]


def test_chord_single_key_rejected():
    with pytest.raises(cu_qmp_backend.UnsupportedText):
        cu_qmp_backend.encode_chord("ctrl")


# --- send_events ------------------------------------------------------------------

@pytest.fixture
def env_dir(tmp_path):
    d = tmp_path / "devin-linux"
    d.mkdir()
    (d / "ready.json").write_text(json.dumps({
        "socket": "tcp://127.0.0.1:1", "token": "t0k",
        "qemu_pid": 1, "daemon_pid": 2}))
    return d


def test_send_events_dispatches_input_send_event(env_dir):
    sent = []

    def ipc(sock, msg, timeout_s, token=None):
        sent.append(msg)
        return {"ok": True, "return": {}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    res = be.send_events(
        cu_qmp_backend.encode_text("hi", layout="en-us"))
    assert res["dispatched"] == 4
    assert sent[0]["command"] == "input-send-event"
    assert sent[0]["arguments"]["events"][0]["data"]["key"]["data"] == "h"


def test_send_events_chunks_long_text(env_dir):
    calls = []

    def ipc(sock, msg, timeout_s, token=None):
        calls.append(len(msg["arguments"]["events"]))
        return {"ok": True, "return": {}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    be.send_events(cu_qmp_backend.encode_text("x" * 60,
                                              layout="en-us"),
                   chunk=50)
    assert calls == [50, 50, 20]  # 120 events total, chunked


def test_lost_ack_releases_held_keys(env_dir):
    """Mid-chord failure: every key seen down must get a release attempt
    — a stuck guest key is worse than a failed send."""
    calls = []

    def flaky(sock, msg, timeout_s, token=None):
        calls.append(msg)
        if len(calls) == 1:
            raise TimeoutError("ack lost")
        return {"ok": True, "return": {}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=flaky)
    with pytest.raises(TimeoutError):
        be.send_events(cu_qmp_backend.encode_chord("ctrl+alt+delete"))
    assert len(calls) == 2  # original + release-all attempt
    ups = calls[1]["arguments"]["events"]
    assert all(e["data"]["down"] is False for e in ups)
    released = {e["data"]["key"]["data"] for e in ups}
    assert released == {"ctrl", "alt", "delete"}


def test_daemon_error_is_typed(env_dir):
    be = cu_qmp_backend.QmpBackend(
        "devin-linux", env_dir=env_dir,
        ipc=lambda s, m, t, token=None: {
            "ok": False, "error_class": "X", "error": "boom"})
    with pytest.raises(cu_qmp_backend.BackendError, match="input"):
        be.send_events(cu_qmp_backend.encode_key("enter"))


# --- type_text remote path: zero host input ---------------------------------------

def test_type_text_remote_never_touches_pynput(env_dir, tmp_path,
                                             monkeypatch, capsys):
    import types
    trap = types.ModuleType("pynput")
    trap.keyboard = None
    monkeypatch.setitem(sys.modules, "pynput", trap)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", trap)

    sent = []

    class FakeBackend:
        env_dir = env_dir

        def send_events(self, events):
            sent.append(events)
            return {"dispatched": len(events)}

    type_text = load("type_text")
    backend = load("cu_backend")
    monkeypatch.setattr(backend, "open_backend",
                        lambda target: FakeBackend())

    reg = tmp_path / "envs"
    reg.mkdir()
    (reg / "devin-linux.json").write_text(json.dumps(
        {"env_id": "devin-linux", "provider": "qemu",
         "keyboard_layout": "en-us"}))
    monkeypatch.setenv("CU_ENV_ROOT", str(reg))
    monkeypatch.setattr(sys, "argv",
                        ["type_text.py", "hello", "--env",
                         "devin-linux"])
    type_text.main()
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is True
    assert out["status"] == "dispatched"
    assert sent and sent[0][0]["data"]["key"]["data"] == "h"
