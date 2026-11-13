"""Held-out native Windows adapter contracts; lead-owned.

Runs on the real host — every child spawned here must be reaped.
"""
import ctypes
from ctypes import wintypes
import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"
PY = sys.executable
pytestmark = pytest.mark.skipif(os.name != "nt", reason="windows only")


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


@pytest.fixture
def win():
    return load("sc_windows")


def _os_start_time(pid):
    """Independent ground truth via GetProcessTimes."""
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not h:
        pytest.fail("cannot open own process")
    try:
        c, e, k, u = (wintypes.FILETIME() for _ in range(4))
        assert ctypes.windll.kernel32.GetProcessTimes(
            h, ctypes.byref(c), ctypes.byref(e),
            ctypes.byref(k), ctypes.byref(u))
        # FILETIME: 100ns ticks since 1601 -> Unix epoch seconds
        return ((c.dwHighDateTime << 32 | c.dwLowDateTime) // 10**7
                - 11644473600)
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def _alive(pid):
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not h:
        return False
    try:
        code = wintypes.DWORD()
        ctypes.windll.kernel32.GetExitCodeProcess(
            h, ctypes.byref(code))
        return code.value == 259  # STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def test_process_identity_matches_os_source(win):
    r = win.process_get(os.getpid())
    assert r["pid"] == os.getpid()
    assert abs(r["start_time"] - _os_start_time(os.getpid())) <= 2


def test_stale_identity_rejected(win):
    try:
        r = win.process_get(os.getpid(), start_time=1)
    except LookupError:
        return
    assert r["status"] == "rejected"


def test_wait_returns_on_child_exit(win):
    proc = subprocess.Popen([PY, "-c", "import time;time.sleep(0.5)"])
    try:
        t0 = time.time()
        r = win.wait_process({"pid": proc.pid,
                              "start_time": _os_start_time(proc.pid)},
                             timeout_s=15)
        assert time.time() - t0 < 14
        assert r["ok"] is True
    finally:
        proc.wait(timeout=10)


def test_spawn_owned_child_dies_with_job(win):
    s = win.spawn_owned([PY, "-c", "import time;time.sleep(60)"])
    try:
        assert s["pid"] > 0
        assert s["start_time"] > 0
    finally:
        win.close_owned(s)
    deadline = time.time() + 8
    while time.time() < deadline:
        if not _alive(s["pid"]):
            break
        time.sleep(0.1)
    else:
        pytest.fail("owned child survived job close")


def test_service_restart_requires_allowlist(win):
    r = win.restart_service("wuauserv", allowed=["some.allowed"])
    assert r["ok"] is False
    assert r["status"] == "rejected"
