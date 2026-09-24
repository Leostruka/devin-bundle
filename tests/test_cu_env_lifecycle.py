"""Gate for C04: VM lifecycle — spec validation, argv build, consent-bound
mutations, instance identity. No real QEMU: spawn/run are injected.
"""
import hashlib
import io
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_env = load("cu_env")
cu_target = load("cu_target")


# --- fixtures -----------------------------------------------------------------

@pytest.fixture
def image(tmp_path):
    img = tmp_path / "live.iso"
    img.write_bytes(b"debian-live-bytes")
    return img


@pytest.fixture
def spec(tmp_path, image):
    return {
        "schema_version": 1,
        "env_id": "devin-linux",
        "provider": "qemu",
        "image_ref": str(image),
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


class _RecordingStdin(io.StringIO):
    """stdin that trips the fake's power flag on system_powerdown."""

    def __init__(self, proc):
        super().__init__()
        self._proc = proc

    def write(self, s):
        if "system_powerdown" in s:
            self._proc.powered_down = True
        return super().write(s)


class FakeProc:
    """Spawned QEMU stand-in: stdin/stdout text pipes + lifecycle."""

    def __init__(self):
        self.powered_down = False
        self.killed = False
        self.stdin = _RecordingStdin(self)
        greeting = json.dumps({"QMP": {"version": {"qemu": {
            "major": 9, "minor": 0, "micro": 0}}, "capabilities": []}})
        self.stdout = io.StringIO(
            greeting + "\r\n" + ('{"return": {}}\r\n' * 5))
        self.pid = 4242
        self.argv = None

    def poll(self):
        return 0 if (self.killed or self.powered_down) else None

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


def _spawn_ok(argv, **kw):
    p = FakeProc()
    p.argv = argv
    return p





def _run_ok(argv, timeout_s=60, **kw):
    return {"returncode": 0, "stdout": "", "stderr": "", "timed_out": False}


def _mgr(root, spec, spawncap=None, ipc=None, consent=None):
    """Manager with all external seams faked. spawn appends to spawncap
    so tests can reach the daemon stand-in; ipc replaces the AF_UNIX
    channel (system_powerdown trips powered_down on the daemon fake)."""
    cap = spawncap if spawncap is not None else []

    def spawn(argv, **kw):
        p = FakeProc()
        p.argv = argv
        cap.append(p)
        return p

    ready = {"qemu_pid": 31337, "daemon_pid": 4242,
             "socket": str(Path(root) / "devin-linux" / "qmp.ipc")}

    if ipc is None:
        def ipc(sock, msg, timeout_s, token=None):
            if msg.get("command") == "system_powerdown" and cap:
                cap[-1].powered_down = True
            return {"ok": True, "return": {}}

    return cu_env.EnvironmentManager(
        spec, root=root, run=_run_ok, spawn=spawn,
        consent=consent or (lambda plan: True),
        wait_ready=lambda t: ready, ipc=ipc)


# --- validate_spec --------------------------------------------------------------

def test_valid_spec_has_no_errors(spec):
    assert cu_env.validate_spec(spec) == []


@pytest.mark.parametrize("field", ["env_id", "image_sha256", "accel",
                                   "qemu_path"])
def test_spec_missing_required_fields(spec, field):
    del spec[field]
    assert any(field in e for e in cu_env.validate_spec(spec))


def test_spec_rejects_bad_digest(spec):
    spec["image_sha256"] = "not-hex"
    assert any("image_sha256" in e for e in cu_env.validate_spec(spec))


def test_spec_rejects_network_on(spec):
    spec["network"] = "user"
    assert any("network" in e for e in cu_env.validate_spec(spec))


def test_spec_rejects_mounts(spec):
    spec["mounts"] = [r"C:\host"]
    assert any("mounts" in e for e in cu_env.validate_spec(spec))


def test_spec_rejects_tcg(spec):
    spec["accel"] = "tcg"
    assert any("accel" in e for e in cu_env.validate_spec(spec))


def test_spec_rejects_traversal_env_id(spec):
    spec["env_id"] = "../evil"
    assert cu_env.validate_spec(spec) != []


# --- build_qemu_argv ------------------------------------------------------------

def test_default_vm_has_no_network(spec, tmp_path):
    overlay = tmp_path / "ov.qcow2"
    argv = cu_env.build_qemu_argv(spec, overlay)
    assert argv[argv.index("-nic") + 1] == "none"
    assert argv[argv.index("-qmp") + 1] == "stdio"
    assert argv[argv.index("-display") + 1] == "none"
    assert argv[argv.index("-monitor") + 1] == "none"
    assert argv[argv.index("-serial") + 1] == "none"
    # a console must exist for screendump — -nodefaults without -vga
    # means no framebuffer at all (real boot proved: "no console")
    assert argv[argv.index("-vga") + 1] == "std"


def test_argv_is_list_no_shell(spec, tmp_path):
    argv = cu_env.build_qemu_argv(spec, tmp_path / "ov.qcow2")
    assert isinstance(argv, list)
    assert all(isinstance(a, str) for a in argv)
    assert argv[0] == spec["qemu_path"]


def test_argv_accel_explicit(spec, tmp_path):
    argv = cu_env.build_qemu_argv(spec, tmp_path / "ov.qcow2")
    assert argv[argv.index("-accel") + 1] == "whpx"


def test_argv_iso_boots_cdrom(spec, tmp_path):
    argv = cu_env.build_qemu_argv(spec, tmp_path / "ov.qcow2")
    assert "-cdrom" in argv
    assert spec["image_ref"] in argv


def test_argv_disk_boot_uses_overlay(spec, tmp_path):
    spec["image_format"] = "qcow2"
    spec["image_ref"] = str(tmp_path / "base.qcow2")
    overlay = tmp_path / "ov.qcow2"
    argv = cu_env.build_qemu_argv(spec, overlay)
    assert any(str(overlay) in a for a in argv)
    assert "-cdrom" not in argv


# --- EnvironmentManager ---------------------------------------------------------

def test_create_makes_overlay_not_base(root, spec, image):
    mgr = _mgr(root, spec)
    mgr.create()
    overlay = mgr.overlay_path
    assert Path(overlay).name == "overlay.qcow2"
    assert str(root) in str(Path(overlay).resolve().parent.resolve())
    # base image untouched
    assert hashlib.sha256(image.read_bytes()).hexdigest() == \
        spec["image_sha256"]


def test_create_without_consent_refuses(root, spec):
    mgr = _mgr(root, spec, consent=lambda plan: False)
    with pytest.raises(cu_env.ConsentDenied):
        mgr.create()


def test_start_records_pid_and_instance(root, spec):
    mgr = _mgr(root, spec)
    mgr.create()
    mgr.start()
    st = mgr.status()
    assert st["pid"] == 4242
    assert st["instance_id"]
    assert st["running"] is True


def test_start_never_adopts_foreign_process(root, spec):
    """No pid file + no spawn = not running; a stray qemu.exe elsewhere is
    never adopted by name."""
    mgr = _mgr(root, spec)
    assert mgr.status()["running"] is False


def test_spec_changed_after_consent_refuses(root, spec):
    mgr = _mgr(root, spec)
    mgr.create()
    spec["resources"]["memory_mib"] = 99999  # mutated post-consent
    with pytest.raises(cu_env.ConsentDenied):
        mgr.start()


def test_overlay_path_outside_root_refused(root, spec, tmp_path):
    mgr = _mgr(root, spec)
    with pytest.raises(ValueError):
        mgr.create(override_overlay=str(tmp_path / "foreign.qcow2"))


def test_swapped_qemu_binary_refused(root, spec, tmp_path):
    fake_qemu = tmp_path / "qemu-system-x86_64.exe"
    fake_qemu.write_bytes(b"swapped-binary")
    spec["qemu_path"] = str(fake_qemu)
    spec["qemu_sha256"] = "0" * 64  # pinned digest no longer matches
    mgr = _mgr(root, spec)
    mgr.create()
    with pytest.raises(cu_env.SpecMismatch):
        mgr.start()


def test_image_digest_mismatch_refuses(root, spec, image):
    spec["image_sha256"] = "1" * 64
    mgr = _mgr(root, spec)
    with pytest.raises(cu_env.SpecMismatch):
        mgr.create()


def test_stop_graceful_via_qmp(root, spec):
    mgr = _mgr(root, spec)
    mgr.create()
    mgr.start()
    mgr.stop()
    st = mgr.status()
    assert st["running"] is False


def test_reset_new_instance_id(root, spec):
    mgr = _mgr(root, spec)
    mgr.create()
    mgr.start()
    first = mgr.status()["instance_id"]
    mgr.reset()
    second = mgr.status()["instance_id"]
    assert first != second
