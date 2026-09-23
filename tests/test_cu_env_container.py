"""C14 — container profile for Linux guests (Xvfb + WM + worker).

Delivery on this host: profile validation + runtime argv builder +
container entry script. Live qualification is a separate matrix line
(native Linux first; WSL2/Docker Desktop are independent rows).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_container = load("cu_container")


def _profile(**over):
    p = {
        "schema_version": 1,
        "env_id": "cu-container",
        "runtime": "podman",
        "image": "cu-guest",
        "image_digest": "sha256:" + "ab" * 32,
        "user": "65534:65534",
        "network": "off",
        "cap_drop": ["ALL"],
        "no_new_privileges": True,
        "read_only_rootfs": True,
        "tmpfs": {"/tmp": "64m"},
        "mounts": [],
        "privileged": False,
        "entry": "container-entry.py",
    }
    p.update(over)
    return p


def test_container_spec_rejects_host_display():
    errors = cu_container.validate_profile(
        _profile(mounts=["/tmp/.X11-unix:/tmp/.X11-unix"]))
    assert "host_display_mount_forbidden" in errors


@pytest.mark.parametrize("mount", [
    "/run/user/1000/bus:/run/user/1000/bus",
    "/run/udev:/run/udev",
    "/dev/input:/dev/input",
    "/dev/uinput:/dev/uinput",
    "/dev/dri:/dev/dri",
    "/mnt/c:/mnt/c",
    "/home/user:/home/user",
    "/run/docker.sock:/run/docker.sock",
    "/var/run/docker.sock:/var/run/docker.sock",
    "/mnt/wslg:/mnt/wslg",
])
def test_forbidden_mounts(mount):
    errors = cu_container.validate_profile(_profile(mounts=[mount]))
    assert errors, f"mount allowed: {mount}"


def test_valid_profile_has_no_errors():
    assert cu_container.validate_profile(_profile()) == []


def test_privileged_rejected():
    assert "privileged_forbidden" in \
        cu_container.validate_profile(_profile(privileged=True))


def test_root_user_rejected():
    errors = cu_container.validate_profile(_profile(user="0:0"))
    assert "root_user_forbidden" in errors
    errors = cu_container.validate_profile(_profile(user="root"))
    assert "root_user_forbidden" in errors


def test_network_must_be_off():
    errors = cu_container.validate_profile(_profile(network="bridge"))
    assert "network_forbidden" in errors


def test_missing_cap_drop_all():
    errors = cu_container.validate_profile(
        _profile(cap_drop=["NET_RAW"]))
    assert "cap_drop_all_required" in errors


def test_no_new_privileges_required():
    errors = cu_container.validate_profile(
        _profile(no_new_privileges=False))
    assert "no_new_privileges_required" in errors


def test_read_only_rootfs_required():
    errors = cu_container.validate_profile(
        _profile(read_only_rootfs=False))
    assert "read_only_rootfs_required" in errors


def test_tmpfs_bounded():
    errors = cu_container.validate_profile(
        _profile(tmpfs={"/tmp": "99999g"}))
    assert "tmpfs_unbounded" in errors


def test_image_digest_required():
    errors = cu_container.validate_profile(_profile(image_digest=None))
    assert "image_digest_required" in errors


def test_runtime_allowlist():
    errors = cu_container.validate_profile(_profile(runtime="runc"))
    assert "runtime_not_allowed" in errors
    assert cu_container.validate_profile(
        _profile(runtime="docker")) == []


def test_unknown_fields_rejected():
    p = _profile()
    p["arbitrary"] = True
    assert "unknown_field:arbitrary" in \
        cu_container.validate_profile(p)


def test_build_run_argv(tmp_path):
    argv = cu_container.build_run_argv(_profile())
    assert isinstance(argv, list)
    assert argv[0] == "podman"
    assert "run" in argv
    assert "--network" in argv and argv[argv.index("--network") + 1] \
        in ("none", "off")
    assert "--user" in argv
    assert "--cap-drop" in argv and "ALL" in argv
    assert "--read-only" in argv
    assert any("no-new-privileges" in a for a in argv)
    assert "--privileged" not in argv
    # image pinned by digest, never a floating tag
    assert "cu-guest@sha256:" + "ab" * 32 in argv


def test_build_run_argv_no_sock(tmp_path):
    argv = cu_container.build_run_argv(_profile())
    joined = " ".join(argv)
    assert "docker.sock" not in joined
    assert "/dev/input" not in joined


def test_docker_runtime_argv():
    argv = cu_container.build_run_argv(_profile(runtime="docker"))
    assert argv[0] == "docker"


def test_validate_then_build_is_safe():
    """build_run_argv on an invalid profile refuses — never half-builds
    a permissive container."""
    with pytest.raises(ValueError):
        cu_container.build_run_argv(_profile(privileged=True))


def test_entry_script_exists():
    entry = Path(__file__).resolve().parents[1] / \
        "extensions" / "computer-use" / "guest" / "container-entry.py"
    assert entry.is_file()
    src = entry.read_text("utf-8")
    assert "Xvfb" in src or "xvfb" in src
