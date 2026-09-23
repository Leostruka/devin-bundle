"""Gate for C05: guest framebuffer capture via QMP screendump — axis
mapping, PPM/PNG parsing, path confinement, IPC observe, and a frontend
path that provably never touches host mss.
"""
import io
import json
import struct
import sys
import threading
import time
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_qmp_backend = load("cu_qmp_backend")
cu_env_daemon = load("cu_env_daemon")


# --- fixtures -----------------------------------------------------------------

def _ppm(w, h, fill=b"\x10\x20\x30"):
    return b"P6\n%d %d\n255\n" % (w, h) + fill * (w * h)


def _png(w, h, rgb=b"\x11\x22\x33", filters=None):
    """Minimal truecolor PNG; filters[i] selects the filter byte per row
    (0=none, 1=sub). Only supports uniform fill + filter 0/1."""
    filters = filters or [0] * h
    raw = bytearray()
    for y in range(h):
        raw.append(filters[y])
        orig = bytearray(rgb * w)
        row = bytearray(orig)
        if filters[y] == 1:  # Sub: encoded[x] = orig[x] - orig[x-bpp]
            for x in range(3, len(row)):
                row[x] = (orig[x] - orig[x - 3]) & 0xFF
        raw += row

    def chunk(ctype, payload):
        c = struct.pack(">I", len(payload)) + ctype + payload
        return c + struct.pack(">I",
                               zlib.crc32(ctype + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b""))


@pytest.fixture
def env_dir(tmp_path):
    d = tmp_path / "devin-linux"
    d.mkdir()
    (d / "ready.json").write_text(json.dumps({
        "socket": str(d / "qmp.ipc"), "qemu_pid": 1,
        "daemon_pid": 2}))
    (d / "state.json").write_text(json.dumps({
        "instance_id": "i-abc123", "running": True}))
    return d


# --- axis mapping ---------------------------------------------------------------

def test_qmp_axis_corners():
    assert cu_qmp_backend.axis_to_qmp(0, 1280) == 0
    assert cu_qmp_backend.axis_to_qmp(1279, 1280) == 32767


def test_qmp_axis_clamps_out_of_range():
    assert cu_qmp_backend.axis_to_qmp(-5, 1280) == 0
    assert cu_qmp_backend.axis_to_qmp(99999, 1280) == 32767


def test_qmp_axis_midpoint_monotonic():
    a = cu_qmp_backend.axis_to_qmp(640, 1280)
    b = cu_qmp_backend.axis_to_qmp(641, 1280)
    assert 0 < a <= b < 32767


# --- frame parsing ----------------------------------------------------------------

def test_parse_ppm_dimensions_and_rgb(tmp_path):
    p = tmp_path / "f.ppm"
    p.write_bytes(_ppm(2, 2))
    img = cu_qmp_backend.parse_frame(p)
    assert (img.width, img.height) == (2, 2)
    assert len(img.rgb) == 12
    assert img.size == (2, 2)


def test_parse_ppm_rejects_bad_raster(tmp_path):
    p = tmp_path / "f.ppm"
    p.write_bytes(_ppm(4, 4)[:-3])
    with pytest.raises(cu_qmp_backend.BackendError):
        cu_qmp_backend.parse_frame(p)


def test_parse_ppm_rejects_huge_geometry(tmp_path):
    p = tmp_path / "f.ppm"
    p.write_bytes(b"P6\n99999 99999\n255\n" + b"\x00" * 12)
    with pytest.raises(cu_qmp_backend.BackendError):
        cu_qmp_backend.parse_frame(p)


def test_parse_png_plain_rows(tmp_path):
    p = tmp_path / "f.png"
    p.write_bytes(_png(3, 2))
    img = cu_qmp_backend.parse_frame(p)
    assert (img.width, img.height) == (3, 2)
    assert img.rgb == b"\x11\x22\x33" * 6


def test_parse_png_sub_filter(tmp_path):
    p = tmp_path / "f.png"
    p.write_bytes(_png(4, 3, filters=[0, 1, 1]))
    img = cu_qmp_backend.parse_frame(p)
    assert img.rgb == b"\x11\x22\x33" * 12


def test_parse_frame_unknown_magic(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"BM" + b"\x00" * 40)
    with pytest.raises(cu_qmp_backend.BackendError):
        cu_qmp_backend.parse_frame(p)


# --- observe ----------------------------------------------------------------------

def _ipc_writes_ppm(sock, msg, timeout_s, token=None):
    Path(msg["arguments"]["filename"]).write_bytes(_ppm(2, 2))
    return {"ok": True, "return": {}}


def test_observe_returns_frame_and_digest(env_dir):
    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=_ipc_writes_ppm)
    img, meta = be.observe()
    assert (img.width, img.height) == (2, 2)
    assert meta["backend"] == "qmp"
    assert meta["instance_id"] == "i-abc123"
    assert len(meta["frame_sha256"]) == 64
    assert meta["env_id"] == "devin-linux"


def test_observe_falls_back_to_ppm_when_png_refused(env_dir):
    calls = []

    def flaky(sock, msg, timeout_s, token=None):
        calls.append(msg["arguments"].get("format"))
        if msg["arguments"].get("format") == "png":
            return {"ok": False, "error_class": "InvalidParameter",
                    "error": "no pixman"}
        Path(msg["arguments"]["filename"]).write_bytes(_ppm(2, 2))
        return {"ok": True, "return": {}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=flaky)
    img, _ = be.observe()
    assert img.width == 2
    assert calls == ["png", None]  # negotiated down, not assumed


def test_observe_daemon_error_is_typed(env_dir):
    be = cu_qmp_backend.QmpBackend(
        "devin-linux", env_dir=env_dir,
        ipc=lambda s, m, t, token=None: {"ok": False, "error_class": "X",
                                         "error": "boom"})
    with pytest.raises(cu_qmp_backend.BackendError, match="screendump"):
        be.observe()


def test_observe_requires_ready_file(tmp_path):
    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=tmp_path,
                                 ipc=_ipc_writes_ppm)
    with pytest.raises(cu_qmp_backend.BackendError, match="env_not_ready"):
        be.observe()


# --- daemon-side confinement --------------------------------------------------------

def test_daemon_confines_screendump_to_env_dir(env_dir):
    out = cu_env_daemon._confined(env_dir, "shot.ppm")
    assert str(env_dir.resolve()) in out


def test_daemon_rejects_foreign_screendump_path(env_dir, tmp_path):
    with pytest.raises(ValueError):
        cu_env_daemon._confined(env_dir, str(tmp_path / "evil.ppm"))


def test_daemon_rejects_traversal_filename(env_dir):
    with pytest.raises(ValueError):
        cu_env_daemon._confined(env_dir, "../../escape.ppm")


# --- frontend: remote capture never touches host mss ---------------------------------

def test_screenshot_remote_ignores_host_mss(env_dir, tmp_path,
                                          monkeypatch, capsys):
    """mss is a trap here — the remote path must capture via the env
    backend only."""
    import types
    trap = types.ModuleType("mss")

    def _boom(*a, **kw):
        raise AssertionError("host mss touched on remote path")

    trap.MSS = _boom
    monkeypatch.setitem(sys.modules, "mss", trap)
    monkeypatch.setitem(sys.modules, "mss.tools", trap)

    screenshot = load("screenshot")
    backend = load("cu_backend")
    monkeypatch.setattr(
        backend, "open_backend",
        lambda target: cu_qmp_backend.QmpBackend(
            "devin-linux", env_dir=env_dir, ipc=_ipc_writes_ppm))

    reg = tmp_path / "envs"
    reg.mkdir()
    (reg / "devin-linux.json").write_text(json.dumps(
        {"env_id": "devin-linux", "provider": "qemu"}))
    monkeypatch.setenv("CU_ENV_ROOT", str(reg))
    out = tmp_path / "shot.png"
    monkeypatch.setattr(sys, "argv",
                        ["screenshot.py", "--env", "devin-linux",
                         "--out", str(out)])
    # PNG encode needs PIL — patch the saver to observe the call instead
    saved = {}
    monkeypatch.setattr(screenshot, "_save_image",
                        lambda im, o, fmt, q: saved.update(path=o))
    screenshot.main()
    res = json.loads(capsys.readouterr().out)
    assert res["ok"] is True
    assert res["backend"] == "qmp"
    assert res["env_id"] == "devin-linux"
    assert res["width"] == 2 and res["height"] == 2
    assert saved["path"] == str(out)


# --- real boundary: daemon + real socket + QMP-fake proc ---------------------------

from collections import deque


class _QmpReader:
    def __init__(self, q):
        self._q = q

    def readline(self):
        return self._q.popleft() if self._q else ""


class _QmpEcho:
    """stdin writer: for each request line, enqueue a QMP-shaped reply —
    bare {"return":{}} for id-less commands (like qmp_capabilities),
    {"id": <rid>, "return":{}} for correlated calls, like real QEMU."""

    def __init__(self, q):
        self._q = q

    def write(self, s):
        for line in s.replace("\r", "").split("\n"):
            if not line:
                continue
            obj = json.loads(line)
            rid = obj.get("id")
            resp = {"return": {}} if rid is None \
                else {"id": rid, "return": {}}
            self._q.append(json.dumps(resp) + "\r\n")
        return len(s)

    def flush(self):
        pass


class _FakeQemu:
    def __init__(self):
        greeting = json.dumps({"QMP": {"version": {"qemu": {}},
                                       "capabilities": []}})
        self._q = deque([greeting + "\r\n"])
        self.stdout = _QmpReader(self._q)
        self.stdin = _QmpEcho(self._q)
        self.killed = False
        self.pid = 9999

    def poll(self):
        return 0 if self.killed else None

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return 0


def _write_approved_spec(env_dir):
    (env_dir / "spec.approved.json").write_text(json.dumps({
        "schema_version": 1, "env_id": "devin-linux", "provider": "qemu",
        "image_ref": "x", "image_sha256": "0" * 64,
        "guest_os": "linux", "keyboard_layout": "en-us",
        "accel": "whpx", "qemu_path": "qemu",
        "resources": {"vcpus": 1, "memory_mib": 512},
        "network": "off", "clipboard": "off",
        "mounts": [], "physical_devices": []}))


def test_daemon_serves_over_real_socket(env_dir):
    _write_approved_spec(env_dir)
    (env_dir / "ready.json").unlink()  # stale fixture entry — daemon
    # must write its own; polling waits for daemon_pid specifically
    qemu = _FakeQemu()
    t = threading.Thread(
        target=cu_env_daemon.serve, args=(env_dir,),
        kwargs={"spawn": lambda argv, **kw: qemu}, daemon=True)
    t.start()
    ready = {}
    for _ in range(100):
        try:
            ready = json.loads(
                (env_dir / "ready.json").read_text())
        except (OSError, json.JSONDecodeError):
            pass
        if ready.get("daemon_pid"):
            break
        time.sleep(0.05)
    assert ready.get("daemon_pid"), "daemon never wrote ready.json"
    assert ready["socket"].startswith("tcp://127.0.0.1:") \
        or "\\pipe\\" not in ready["socket"]

    resp = cu_qmp_backend.ipc_call(
        ready["socket"], {"command": "query-status"}, 5,
        token=ready.get("token"))
    assert resp == {"ok": True, "return": {}}

    if ready.get("token"):
        bad = cu_qmp_backend.ipc_call(
            ready["socket"], {"command": "query-status"}, 5,
            token="wrong-token")
        assert bad["ok"] is False
        assert "unauthorized" in bad["error"]
    qemu.kill()
