"""Gate for C00: read-only environment doctor.

doctor() inspects prerequisites (QEMU binary, version, accelerators,
resources, explicitly-indicated image) and never mutates the machine:
no installs, no drivers, no VM started, no Windows feature enabled.
`which`/`run` are injected seams; production defaults live in cu_env.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_env = cu_load.load("cu_env")

QEMU_PATH = r"C:\qemu\qemu-system-x86_64.exe"


def forbidden_run(*args, **kwargs):
    raise AssertionError("doctor must not spawn processes in this path")


def _res(rc, out="", err="", timed_out=False):
    return {"returncode": rc, "stdout": out, "stderr": err,
            "timed_out": timed_out}


def _which_ok(name):
    return QEMU_PATH if "qemu-system" in name else None


def _run_all_good(argv, timeout_s=10):
    joined = " ".join(argv)
    if "--version" in joined:
        return _res(0, "QEMU emulator version 9.0.0\n")
    if "help" in joined and "-accel" in joined:
        return _res(0, "Accelerators supported in QEMU binaries:\n"
                       "tcg\nwhpx\n")
    # accel init probe: staying alive past the deadline means it initialized
    return _res(0, "", "", timed_out=True)


def test_missing_qemu_does_not_provision():
    report = cu_env.doctor(which=lambda name: None, run=forbidden_run)
    assert report["ready"] is False
    assert report["actions_performed"] == []
    assert report["required_user_actions"]
    assert report["qemu"]["path"] is None


def test_accelerator_listed_but_probe_fails_is_not_ready():
    def run(argv, timeout_s=10):
        joined = " ".join(argv)
        if "--version" in joined:
            return _res(0, "QEMU emulator version 9.0.0\n")
        if "help" in joined:
            return _res(0, "tcg\nwhpx\n")
        return _res(1, "", "whpx: accelerator not supported")

    report = cu_env.doctor(which=_which_ok, run=run, sysname="Windows")
    assert report["ready"] is False
    assert "whpx" in report["accelerators"]["listed"]
    assert report["accelerators"]["verified"] == []
    assert report["actions_performed"] == []


def test_tcg_only_is_not_a_silent_fallback():
    def run(argv, timeout_s=10):
        joined = " ".join(argv)
        if "--version" in joined:
            return _res(0, "QEMU emulator version 9.0.0\n")
        if "help" in joined:
            return _res(0, "tcg\n")
        return _res(0, "", "", timed_out=True)

    report = cu_env.doctor(which=_which_ok, run=run, sysname="Windows")
    assert report["ready"] is False
    assert report["accelerators"]["listed"] == ["tcg"]
    assert "whpx" not in report["accelerators"]["verified"]
    assert any("accel" in a.lower() or "whpx" in a.lower()
               for a in report["required_user_actions"])


def test_happy_path_reports_verified_accelerator():
    report = cu_env.doctor(which=_which_ok, run=_run_all_good,
                           sysname="Windows")
    assert report["ready"] is True
    assert report["qemu"]["version"].startswith("9.")
    assert "whpx" in report["accelerators"]["verified"]
    assert report["actions_performed"] == []


def test_unapproved_image_is_rejected(tmp_path):
    img = tmp_path / "base.qcow2"
    img.write_bytes(b"not-the-approved-image")

    report = cu_env.doctor(which=_which_ok, run=_run_all_good,
                           sysname="Windows",
                           image_path=str(img), image_sha256="0" * 64)
    assert report["ready"] is False
    assert report["image"]["approved"] is False
    assert report["actions_performed"] == []


def test_missing_indicated_image_is_not_ready(tmp_path):
    report = cu_env.doctor(which=_which_ok, run=_run_all_good,
                           sysname="Windows",
                           image_path=str(tmp_path / "absent.qcow2"))
    assert report["ready"] is False
    assert report["image"]["present"] is False


def test_subprocess_timeout_is_reported_not_raised():
    def run(argv, timeout_s=10):
        return _res(-1, "", "", timed_out=True)

    report = cu_env.doctor(which=_which_ok, run=run, sysname="Windows")
    assert report["ready"] is False
    assert report["actions_performed"] == []


def test_run_exception_is_reported_not_raised():
    def run(argv, timeout_s=10):
        raise OSError("spawn failed")

    report = cu_env.doctor(which=_which_ok, run=run, sysname="Windows")
    assert report["ready"] is False
    assert report["actions_performed"] == []


def test_accel_probe_uses_real_frozen_machine():
    """`-machine none` is not a valid accel target on QEMU ≥11 — the probe
    must run a real machine with the CPU frozen (-S, -nodefaults)."""
    seen = []

    def run(argv, timeout_s=10):
        seen.append(argv)
        joined = " ".join(argv)
        if "--version" in joined:
            return _res(0, "QEMU emulator version 11.1.0\n")
        if "help" in joined:
            return _res(0, "tcg\nwhpx\n")
        return _res(0, "", "", timed_out=True)

    cu_env.doctor(which=_which_ok, run=run, sysname="Windows")
    probe = next(a for a in seen if "-S" in a)
    assert probe[probe.index("-machine") + 1] != "none"
    assert "-nodefaults" in probe


def test_linux_prefers_kvm():
    def run(argv, timeout_s=10):
        joined = " ".join(argv)
        if "--version" in joined:
            return _res(0, "QEMU emulator version 9.0.0\n")
        if "help" in joined:
            return _res(0, "kvm\ntcg\n")
        return _res(0, "", "", timed_out=True)

    report = cu_env.doctor(which=_which_ok, run=run, sysname="Linux")
    assert report["ready"] is True
    assert report["accelerators"]["preferred"] == "kvm"
