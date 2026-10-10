"""craft-bridge — CLI dispatch, control channel, manifest compile.

No real craft binaries in CI: a fake `fakecraft-cli` python script on a
temp PATH and a local JSON-lines TCP stub exercise both channels.
"""
import json
import socket
import sys
import threading
from pathlib import Path

import pytest

CB_DIR = Path(__file__).resolve().parents[1] / "extensions" / "craft-bridge"
sys.path.insert(0, str(CB_DIR))

import bridge                    # noqa: E402
import scene_manifest as sm      # noqa: E402


FAKE_CLI = """\
import json, sys
args = sys.argv[1:]
if args and args[0] == "commands":
    print("timeline.cut\\nfile.export\\nfile.open")
    sys.exit(0)
if args[:2] == ["run", "--command"]:
    out = {"ran": args[2], "params": json.loads(
        args[args.index("--params") + 1]) if "--params" in args else {}}
    print(json.dumps(out)); sys.exit(0)
sys.exit(2)
"""


@pytest.fixture
def fake_app(tmp_path, monkeypatch):
    script = tmp_path / "fakecraft_cli.py"
    script.write_text(FAKE_CLI)
    monkeypatch.setitem(
        bridge.APPS, "fakecraft",
        {"cli": [sys.executable, str(script)], "domain": "fake"})

    def _which(name):
        return name if name == sys.executable else None
    monkeypatch.setattr(bridge.shutil, "which", _which)
    return "fakecraft"


# --- bridge -------------------------------------------------------------------

def test_doctor_marks_missing_apps():
    rep = bridge.doctor()
    assert set(rep) == set(bridge.APPS)
    assert all("found" in v for v in rep.values())


def test_list_commands_uses_cli(fake_app):
    r = bridge.list_commands(fake_app)
    assert r["ok"] and "timeline.cut" in r["stdout"]


def test_run_command_passes_params(fake_app):
    r = bridge.run_command(fake_app, "timeline.cut", {"at_s": 2.0})
    assert r["ok"]
    ran = json.loads(r["stdout"])
    assert ran["ran"] == "timeline.cut"
    assert ran["params"] == {"at_s": 2.0}


def test_run_command_missing_cli_errors():
    r = bridge.run_command("filmcraft", "x")
    assert r["ok"] is False and "not on PATH" in r["error"]


def test_unknown_app_raises():
    with pytest.raises(KeyError):
        bridge.cli_path("notacraft")


# --- control channel ------------------------------------------------------------

class _StubServer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.received = None

    def run(self):
        conn, _ = self.sock.accept()
        data = b""
        while b"\n" not in data:
            data += conn.recv(4096)
        self.received = json.loads(data.decode().strip())
        conn.sendall((json.dumps(
            {"id": self.received["id"], "ok": True,
             "result": {"done": True}}) + "\n").encode())
        conn.close()
        self.sock.close()


def test_control_channel_roundtrip():
    srv = _StubServer()
    srv.start()
    ch = bridge.ControlChannel("vectorcraft", port=srv.port)
    r = ch.call("shape.rect", {"w": 10})
    srv.join(5)
    assert r["ok"] and r["result"]["done"]
    assert srv.received["command"] == "shape.rect"


def test_control_channel_requires_port():
    with pytest.raises(ValueError):
        bridge.ControlChannel("filmcraft")


# --- scene manifest ---------------------------------------------------------------

def test_compile_routes_layers_and_marks_unverified():
    m = {"version": 1, "scenes": [
        {"id": "s1", "layers": [
            {"type": "video", "source": "a.mp4",
             "ops": [{"op": "cut", "params": {"at_s": 2}}]},
            {"type": "image", "source": "b.psd",
             "ops": [{"op": "frobnicate"}]},
            {"type": "hologram", "source": "c.holo"}]}]}
    out = sm.compile(m)
    assert out["ok"]
    plan = out["plan"]
    assert plan[0]["app"] == "filmcraft"
    assert plan[0]["command"] == "timeline.cut"
    assert plan[1]["app"] == "photocraft"
    assert plan[1]["unverified"] is True
    assert any("unrouted_layer_type:hologram" in n for n in out["notes"])


def test_compile_rejects_wrong_version():
    assert sm.compile({"version": 2})["ok"] is False


def test_default_op_is_open():
    m = {"version": 1, "scenes": [
        {"id": "s", "layers": [{"type": "pdf", "source": "x.pdf"}]}]}
    out = sm.compile(m)
    assert out["plan"][0]["command"] == "file.open"
