#!/usr/bin/env python3
"""Container profile for isolated Linux guests (C14).

A container env runs Xvfb + a window manager + the guest worker inside
a locked-down OCI container: private display, no host X11/Wayland/DBus
sockets, no host device nodes, no docker.sock, network off.

`validate_profile(profile) -> list[str]` is an allowlist validator:
every field must be known, every requirement explicit — permissive
defaults are errors, not conveniences. `build_run_argv` refuses to
emit argv for an invalid profile.

Live qualification is a separate matrix line (native Linux first);
this module only guarantees the spec is closed and the runtime argv
matches it exactly.
"""
import re
from pathlib import Path

ALLOWED_RUNTIMES = frozenset({"docker", "podman"})

_ALLOWED_FIELDS = frozenset({
    "schema_version", "env_id", "runtime", "image", "image_digest",
    "user", "network", "cap_drop", "cap_add", "no_new_privileges",
    "read_only_rootfs", "tmpfs", "mounts", "privileged", "entry",
    "env", "pids_limit", "memory_mib",
})

# Host surfaces that must never enter the container: display servers,
# input device nodes, GPU, the container runtime's own control socket,
# WSLg interop, host homes and Windows mounts.
_FORBIDDEN_MOUNT = (
    (re.compile(r"^/tmp/\.X11-unix"), "host_display_mount_forbidden"),
    (re.compile(r"\.(wayland|weston)|/run/wayland"),
     "host_display_mount_forbidden"),
    (re.compile(r"/(run/)?dbus|/run/user/\d+/bus"),
     "host_dbus_mount_forbidden"),
    (re.compile(r"^/dev/input"), "host_input_mount_forbidden"),
    (re.compile(r"^/dev/uinput"), "host_input_mount_forbidden"),
    (re.compile(r"^/dev/dri"), "host_gpu_mount_forbidden"),
    (re.compile(r"^/run/udev|^/dev/?$|^/dev/"),
     "host_device_mount_forbidden"),
    (re.compile(r"docker\.sock|podman\.sock|containerd\.sock"),
     "runtime_socket_forbidden"),
    (re.compile(r"/mnt/wslg|wslg"), "wslg_mount_forbidden"),
    (re.compile(r"^/mnt/[a-zA-Z]($|/)"), "host_fs_mount_forbidden"),
    (re.compile(r"^/home($|/)|^/root($|/)|^/Users($|/)"),
     "host_home_mount_forbidden"),
)

_TMPFS_MAX_MIB = 256
_SIZE_RE = re.compile(r"^(\d+)([kmg]?)(b?)$", re.I)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _size_mib(s):
    m = _SIZE_RE.match(str(s).strip())
    if not m:
        return None
    n = int(m.group(1))
    mult = {"": 1 / (1024 * 1024), "k": 1 / 1024,
            "m": 1, "g": 1024}[m.group(2).lower()]
    return n * mult


def _is_root_user(user):
    u = str(user or "").strip()
    if not u:
        return True
    name = u.split(":", 1)[0]
    return name in ("0", "root")


def _check_mount(spec):
    """Return the error code for a forbidden mount, else None."""
    src = str(spec).split(":", 1)[0]
    for rx, code in _FORBIDDEN_MOUNT:
        if rx.search(src):
            return code
    return None


def validate_profile(profile):
    """List of error strings; [] = consumable. Closed profile: unknown
    fields, privileged mode, host mounts, root user, shared network and
    floating images are all rejected."""
    errors = []
    if not isinstance(profile, dict):
        return ["profile_not_a_mapping"]
    if profile.get("schema_version") != 1:
        errors.append("schema_version: must be 1")
    for key in profile:
        if key not in _ALLOWED_FIELDS:
            errors.append(f"unknown_field:{key}")
    try:
        import cu_target
        cu_target._check_component(profile.get("env_id"), "env_id")
    except (ValueError, ImportError):
        errors.append("env_id: missing or unsafe component")
    if profile.get("runtime") not in ALLOWED_RUNTIMES:
        errors.append("runtime_not_allowed")
    if not isinstance(profile.get("image"), str) or not profile["image"]:
        errors.append("image_required")
    digest = profile.get("image_digest")
    if not isinstance(digest, str) or not _DIGEST_RE.match(digest):
        errors.append("image_digest_required")
    if _is_root_user(profile.get("user")):
        errors.append("root_user_forbidden")
    if profile.get("network") != "off":
        errors.append("network_forbidden")
    if "ALL" not in (profile.get("cap_drop") or []):
        errors.append("cap_drop_all_required")
    if profile.get("cap_add"):
        errors.append("cap_add_forbidden")
    if profile.get("no_new_privileges") is not True:
        errors.append("no_new_privileges_required")
    if profile.get("read_only_rootfs") is not True:
        errors.append("read_only_rootfs_required")
    if profile.get("privileged"):
        errors.append("privileged_forbidden")
    mounts = profile.get("mounts") or []
    if not isinstance(mounts, list):
        errors.append("mounts: must be a list")
    else:
        for mnt in mounts:
            code = _check_mount(mnt)
            if code:
                errors.append(code)
    tmpfs = profile.get("tmpfs") or {}
    if not isinstance(tmpfs, dict):
        errors.append("tmpfs: must be a mapping")
    else:
        for dest, size in tmpfs.items():
            mib = _size_mib(size)
            if mib is None or mib > _TMPFS_MAX_MIB:
                errors.append("tmpfs_unbounded")
                break
            if not str(dest).startswith("/"):
                errors.append("tmpfs_dest_absolute_required")
                break
    if not isinstance(profile.get("entry"), str) or not profile["entry"]:
        errors.append("entry_required")
    return errors


def build_run_argv(profile):
    """argv for `<runtime> run` matching the validated profile exactly.
    Refuses invalid profiles — a half-built permissive container is
    worse than none."""
    errors = validate_profile(profile)
    if errors:
        raise ValueError("invalid_profile:" + ";".join(errors))
    image = f"{profile['image']}@{profile['image_digest']}"
    argv = [profile["runtime"], "run", "--rm", "-i",
            "--name", f"cu-{profile['env_id']}",
            "--network", "none",
            "--user", profile["user"],
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--read-only"]
    for dest, size in (profile.get("tmpfs") or {}).items():
        argv += ["--tmpfs", f"{dest}:rw,size={size}"]
    if profile.get("pids_limit"):
        argv += ["--pids-limit", str(profile["pids_limit"])]
    if profile.get("memory_mib"):
        argv += ["--memory", f"{profile['memory_mib']}m"]
    for k, v in (profile.get("env") or {}).items():
        argv += ["-e", f"{k}={v}"]
    argv.append(image)
    argv += ["python3", f"/opt/cu/guest/{profile['entry']}"]
    return argv
