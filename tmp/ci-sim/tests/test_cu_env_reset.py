"""C13 — stop/reset/restart semantics.

stop    = graceful shutdown of the SAME instance (session id stable
          while the instance lives; observation requires same boot).
restart = same instance_id, QEMU process recycled.
reset   = NEW instance_id + fresh overlay; old runtime archived, not
          left to collide. Forced termination is a distinct, disclosed
          operation — never silent.
"""
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_env = load("cu_env")


@pytest.fixture
def spec(tmp_path):
    img = tmp_path / "live.iso"
    img.write_bytes(b"debian-live-bytes")
    return {
        "schema_version": 1,
        "env_id": "devin-linux",
        "provider": "qemu",
        "image_ref": str(img),
        "image_sha256": hashlib.sha256(b"debian-live-bytes").hexdigest(),
        "image_format": "iso",
        "guest_os": "linux",
        "keyboard_layout": "en-us",
        "accel": "whpx",
        "qemu_path": r"C:\qemu\qemu-system-x86_64.exe",
        "resources": {"vcpus": 2, "memory_mib": 4096},
        "network": "off",
        "clipboard": "off",
        "mounts": [],
        "physical_devices": [],
    }


@pytest.fixture
def root(tmp_path, monkeypatch):
    r = tmp_path / "cu-envs"
    monkeypatch.setenv("CU_STATE_ROOT", str(r))
    return r


class FakeProc:
    def __init__(self):
        self.killed = False
        self.pid = 4242

    def poll(self):
        return 0 if self.killed else None

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


def _dead_pid():
    """A pid guaranteed exited — deterministic liveness checks."""
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def _run_ok(argv, timeout_s=60, **kw):
    # qemu-img create ... <path> <size>M — materialize the overlay
    if "create" in argv:
        Path(argv[-2]).write_bytes(b"qcow2")
    return {"returncode": 0, "stdout": "", "stderr": "",
            "timed_out": False}


def _mgr(spec, root, ipc=None, spawncap=None):
    cap = spawncap if spawncap is not None else []

    def spawn(argv, **kw):
        p = FakeProc()
        cap.append(p)
        return p

    ready = {"qemu_pid": 31337, "daemon_pid": 4242,
             "socket": "x", "token": "t"}
    if ipc is None:
        def ipc(sock, msg, timeout_s, token=None):
            return {"ok": True, "return": {}}
    return cu_env.EnvironmentManager(
        spec, root=root, run=_run_ok, spawn=spawn,
        consent=lambda plan: True,
        wait_ready=lambda t: ready, ipc=ipc)


def _live_state(mgr, iid="i-1"):
    return {"env_id": "devin-linux", "running": True,
            "pid": _dead_pid(), "qemu_pid": 31337,
            "socket": "x", "token": "t",
            "instance_id": iid, "session_id": "default",
            "spec_sha256": cu_env.spec_digest(mgr.spec)}


def test_restart_same_instance_new_process(spec, root):
    cap = []
    m = _mgr(spec, root, spawncap=cap)
    (root / "devin-linux").mkdir(parents=True)
    m.state_file().write_text(json.dumps(_live_state(m)))
    r = m.restart()
    assert r["running"] is True
    assert r["instance_id"] == "i-1"      # same instance
    assert r["session_id"] == "default"   # same session
    assert len(cap) == 1                  # new daemon process


def test_stop_then_start_same_instance(spec, root):
    m = _mgr(spec, root)
    (root / "devin-linux").mkdir(parents=True)
    m.state_file().write_text(json.dumps(_live_state(m)))
    r = m.stop()
    assert r["running"] is False
    r2 = m.start()
    assert r2["instance_id"] == "i-1"


def test_reset_new_instance_and_archives_old(spec, root):
    m = _mgr(spec, root)
    env_dir = root / "devin-linux"
    env_dir.mkdir(parents=True)
    m.state_file().write_text(json.dumps(_live_state(m, iid="i-old")))
    (env_dir / "overlay.qcow2").write_bytes(b"old-disk")
    r = m.reset()
    assert r["instance_id"] != "i-old"
    assert (env_dir / "overlay.qcow2").exists()        # fresh overlay
    assert (env_dir / "instances" / "i-old"
            / "state.json").exists()                  # preserved


def test_stop_is_graceful_not_kill(spec, root):
    calls = []

    def ipc(sock, msg, timeout_s, token=None):
        calls.append(msg.get("command"))
        return {"ok": True, "return": {}}

    m = _mgr(spec, root, ipc=ipc)
    (root / "devin-linux").mkdir(parents=True)
    m.state_file().write_text(json.dumps(_live_state(m)))
    r = m.stop()
    assert r["running"] is False
    assert "system_powerdown" in calls
    assert "quit" not in calls      # graceful only; force is separate


def test_force_stop_is_distinct_and_disclosed(spec, root):
    def dead_ipc(sock, msg, timeout_s, token=None):
        raise RuntimeError("dead")

    m = _mgr(spec, root, ipc=dead_ipc)
    (root / "devin-linux").mkdir(parents=True)
    m.state_file().write_text(json.dumps(_live_state(m)))
    r = m.stop()
    assert r["status"] == "unknown"          # dead daemon ≠ confirmed stop
    rf = m.stop(force=True)
    assert rf["running"] is False
    assert rf.get("forced") is True          # disclosed


def test_reset_invalidates_old_instance():
    assert cu_env.same_instance({"instance_id": "before"},
                                {"instance_id": "after"}) is False
    assert cu_env.same_instance({"instance_id": "a"},
                                {"instance_id": "a"}) is True
    assert cu_env.same_instance({}, {"instance_id": "a"}) is False
    assert cu_env.same_instance({"instance_id": ""},
                                {"instance_id": ""}) is False


def test_inconsistent_state_terminal_error(spec, root):
    m = _mgr(spec, root)
    (root / "devin-linux").mkdir(parents=True)
    st = _live_state(m)
    st["instance_id"] = ""                   # corrupted
    m.state_file().write_text(json.dumps(st))
    with pytest.raises(RuntimeError, match="state_inconsistent"):
        m.status()
