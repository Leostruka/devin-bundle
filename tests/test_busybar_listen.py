"""busybar listen — event mapping + replay (#491)."""
import importlib.util
import json
import os
import sys

spec = importlib.util.spec_from_file_location(
    "busybar_listen",
    os.path.join(os.path.dirname(__file__), "..", "extensions",
                 "busybar", "listen.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["busybar_listen"] = mod
spec.loader.exec_module(mod)


def test_map_switch_toggle():
    assert mod.map_event({"switch": "star", "pressed": True}) == \
        "focus-start"
    assert mod.map_event({"switch": "star",
                          "pressed": False}) == "focus-stop"
    assert mod.map_event({"button": "pause", "state": "off"}) == \
        "focus-stop"


def test_map_dial_effort():
    assert mod.map_event({"dial": 1}) == "effort-S"
    assert mod.map_event({"encoder": {"position": 3}}) == "effort-L"
    assert mod.map_event({"dial": 9}) is None


def test_unknown_frames_ignored():
    assert mod.map_event({"type": "audio", "level": 5}) is None
    assert mod.map_event({}) is None


def test_replay_counts_actions_and_skips_bad(tmp_path, capsys,
                                             monkeypatch):
    monkeypatch.chdir(tmp_path)  # effort preset writes .devin/ here
    f = tmp_path / "f.jsonl"
    f.write_text('\n'.join([
        json.dumps({"switch": "star", "pressed": True}),
        "garbage{",
        json.dumps({"dial": 2}),
        json.dumps({"type": "noop"}),
    ]), encoding="utf-8")
    mod.replay(str(f), exec_mode=False)
    out = capsys.readouterr()
    assert '"actions": 2' in out.out
    assert "unreadable frame skipped" in out.err


def _frame(payload: bytes) -> bytes:
    """RFC6455 unmasked server text frame, small payloads only."""
    return bytes([0x81, len(payload)]) + payload


def test_ws_loopback_receives_bundled_frame(capsys, tmp_path,
                                            monkeypatch):
    monkeypatch.chdir(tmp_path)  # effort preset writes .devin/ here
    """Loopback ws:// server: handshake + text frame in ONE packet —
    the regression case for the post-handshake leftover buffer."""
    import socket
    import threading

    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        conn, _ = srv.accept()
        conn.recv(4096)  # the upgrade request
        conn.sendall(
            b"HTTP/1.1 101 Switching Protocols\r\n"
            b"Upgrade: websocket\r\nConnection: Upgrade\r\n\r\n"
            + _frame(json.dumps(
                {"switch": "star", "pressed": True}).encode())
            + _frame(b"garbage{")
            + _frame(json.dumps({"dial": 3}).encode())
            + bytes([0x88, 0]))  # close frame
        conn.close()
        srv.close()

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    mod.listen_ws(f"ws://127.0.0.1:{port}/stream", exec_mode=False)
    t.join(timeout=5)
    out = capsys.readouterr().out
    assert "focus-start" in out
    assert "effort preset -> L (persisted)" in out
    assert (tmp_path / ".devin" / "busybar-effort.txt").read_text(
        encoding="utf-8") == "L"
