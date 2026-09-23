#!/usr/bin/env python3
"""Environment prerequisites — read-only doctor.

doctor(which, run, ...) -> report dict
  Inspects platform, QEMU binary, version, announced vs initialized
  accelerators, free disk/RAM, and an explicitly-indicated image.
  Never installs, never enables OS features, never starts a VM:
  `actions_performed` is always []. Deficiencies land in
  `required_user_actions` for a human to resolve.

`run` seam: run(argv, timeout_s) ->
  {"returncode": int, "stdout": str, "stderr": str, "timed_out": bool}
  The accel init probe relies on `-machine none`: a process that stays
  alive past the deadline initialized the accelerator (subprocess.run
  kills it); a fast non-zero exit means it did not. TCG is never a
  substitute for the platform accelerator.
"""
import hashlib
import os
import platform
import re
import shutil
import subprocess
import tempfile

ACCEL_PREFERRED = {"Windows": "whpx", "Linux": "kvm", "Darwin": "hvf"}
_ACCEL_HELP_RE = re.compile(r"^[a-z0-9_-]+$")
_VERSION_RE = re.compile(r"version (\d+\.\d+\.\d+)")


def _default_run(argv, timeout_s=10):
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout_s)
        return {"returncode": proc.returncode, "stdout": proc.stdout,
                "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "",
                "timed_out": True}


def _qemu_binary(machine):
    arch = {"AMD64": "x86_64", "x86_64": "x86_64",
            "ARM64": "aarch64", "aarch64": "aarch64"}.get(machine, "x86_64")
    return f"qemu-system-{arch}"


def _parse_accel_listing(text):
    out = []
    for line in text.splitlines():
        tok = line.strip().lower()
        if _ACCEL_HELP_RE.match(tok):
            out.append(tok)
    return out


def _probe_accel(run, qemu_path, accel, timeout_s):
    argv = [qemu_path, "-machine", "none", "-accel", accel,
            "-display", "none", "-monitor", "none"]
    res = run(argv, timeout_s)
    return res["timed_out"] or res["returncode"] == 0


def _free_ram_mib(sysname):
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_AVPHYS_PAGES")
            return pages * os.sysconf("SC_PAGE_SIZE") // (1024 * 1024)
        if sysname == "Windows":
            import ctypes

            class _Mem(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong),
                            ("memory_load", ctypes.c_ulong),
                            ("total_phys", ctypes.c_ulonglong),
                            ("avail_phys", ctypes.c_ulonglong),
                            ("total_pf", ctypes.c_ulonglong),
                            ("avail_pf", ctypes.c_ulonglong),
                            ("total_virt", ctypes.c_ulonglong),
                            ("avail_virt", ctypes.c_ulonglong),
                            ("avail_ext_virt", ctypes.c_ulonglong)]

            st = _Mem()
            st.length = ctypes.sizeof(_Mem)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return st.avail_phys // (1024 * 1024)
    except (ValueError, OSError, AttributeError):
        pass
    return None


def _check_image(image_path, image_sha256):
    if image_path is None:
        return None
    entry = {"path": image_path, "present": False,
             "sha256": None, "approved": False}
    if not os.path.isfile(image_path):
        return entry
    entry["present"] = True
    if image_sha256 is None:
        return entry
    digest = hashlib.sha256()
    with open(image_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    entry["sha256"] = digest.hexdigest()
    entry["approved"] = entry["sha256"] == image_sha256.lower()
    return entry


def doctor(which=None, run=None, sysname=None, image_path=None,
           image_sha256=None, disk_path=None, probe_timeout_s=5):
    """Read-only prerequisite report; performs zero mutations."""
    which = which or shutil.which
    run = run or _default_run
    sysname = sysname or platform.system()
    machine = platform.machine()

    report = {"schema_version": 1, "provider": "qemu", "ready": False,
              "platform": {"system": sysname, "machine": machine,
                           "python": platform.python_version()},
              "qemu": {"path": None, "version": None},
              "accelerators": {"listed": [], "verified": [],
                               "preferred": ACCEL_PREFERRED.get(sysname)},
              "resources": {"disk_free_mib": None, "ram_mib_free": None},
              "image": None,
              "required_user_actions": [],
              "actions_performed": []}
    actions = report["required_user_actions"]

    try:
        usage = shutil.disk_usage(disk_path or tempfile.gettempdir())
        report["resources"]["disk_free_mib"] = usage.free // (1024 * 1024)
    except OSError:
        pass
    report["resources"]["ram_mib_free"] = _free_ram_mib(sysname)

    qemu_path = which(_qemu_binary(machine))
    if not qemu_path:
        actions.append("install_qemu: qemu-system binary not found on PATH")
        report["image"] = _check_image(image_path, image_sha256)
        return report
    report["qemu"]["path"] = qemu_path

    try:
        res = run([qemu_path, "--version"], 15)
        m = _VERSION_RE.search(res["stdout"])
        if m:
            report["qemu"]["version"] = m.group(1)
        else:
            actions.append("qemu_version_unreadable: reinstall or fix QEMU")
            report["image"] = _check_image(image_path, image_sha256)
            return report
    except Exception as exc:  # spawn/timeout failures are data, not crashes
        actions.append(f"qemu_probe_failed: {type(exc).__name__}")
        report["image"] = _check_image(image_path, image_sha256)
        return report

    try:
        res = run([qemu_path, "-accel", "help"], 15)
        report["accelerators"]["listed"] = _parse_accel_listing(
            res["stdout"] + "\n" + res["stderr"])
    except Exception as exc:
        actions.append(f"accel_listing_failed: {type(exc).__name__}")

    preferred = report["accelerators"]["preferred"]
    if preferred and preferred in report["accelerators"]["listed"]:
        try:
            if _probe_accel(run, qemu_path, preferred, probe_timeout_s):
                report["accelerators"]["verified"].append(preferred)
            else:
                actions.append(
                    f"enable_accelerator: {preferred} listed but failed "
                    "to initialize")
        except Exception as exc:
            actions.append(f"accel_probe_failed: {type(exc).__name__}")
    elif preferred:
        actions.append(
            f"enable_accelerator: {preferred} not announced by QEMU")
    else:
        actions.append(f"unknown_platform_accelerator: {sysname}")

    report["image"] = _check_image(image_path, image_sha256)
    if report["image"] is None:
        actions.append("indicate_approved_image: no image_path given")
    elif not report["image"]["present"]:
        actions.append("image_missing: indicated image not found")
    elif not report["image"]["approved"]:
        actions.append("image_not_approved: sha256 missing or mismatched")

    report["ready"] = (
        report["qemu"]["version"] is not None
        and preferred in report["accelerators"]["verified"]
        and (report["image"] is None
             or (report["image"]["present"] and report["image"]["approved"]))
    )
    return report
