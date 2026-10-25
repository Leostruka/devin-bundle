"""Tests for the detached cu task runner + trace store."""

import json
import os
import subprocess
import sys
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(REPO, "extensions", "computer-use", "cu_taskrunner.py")


def _cli(*args, timeout=20):
    return subprocess.run([sys.executable, RUNNER, *args],
                          capture_output=True, text=True, timeout=timeout,
                          cwd=REPO)


@pytest.fixture
def store(monkeypatch, tmp_path):
    """Redirect the trace store to tmp."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cu_taskrunner", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "STORE", str(tmp_path / "cu_tasks"))
    return mod


def _wait_terminal(store, tid, timeout=15):
    deadline = time.time() + timeout
    st = None
    while time.time() < deadline:
        st = store.status(tid)
        if st and st["state"] in ("done", "failed", "stopped"):
            break
        time.sleep(0.3)
    return st


def test_start_status_done(store):
    tid = store.start([sys.executable, "-c", "print('hello')"])
    assert len(tid) == 12
    st = _wait_terminal(store, tid)
    assert st["state"] == "done", st
    assert st["ended"] is not None
    with open(os.path.join(store.STORE, tid, "stdout.log"),
              encoding="utf-8") as f:
        assert "hello" in f.read()


def test_failed_returncode(store):
    tid = store.start([sys.executable, "-c", "import sys; sys.exit(3)"])
    st = _wait_terminal(store, tid)
    assert st["state"] == "failed", st
    assert st["returncode"] == 3


def test_stop_running_task(store):
    tid = store.start([sys.executable, "-c", "import time; time.sleep(60)"])
    deadline = time.time() + 15
    st = None
    while time.time() < deadline:
        st = store.status(tid)
        if st and st["state"] == "running":
            break
        time.sleep(0.2)
    assert st["state"] == "running", st
    res = store.stop(tid)
    assert res["state"] == "stopped"
    assert store.status(tid)["state"] == "stopped"


def test_list_and_missing(store):
    assert store.status("deadbeef0000") is None
    tid = store.start([sys.executable, "-c", "pass"])
    ids = [t["trace_id"] for t in store.list_tasks()]
    assert tid in ids


def test_cli_surface(tmp_path):
    p = _cli("start", "--", sys.executable, "-c", "print(1)")
    assert p.returncode == 0
    tid = p.stdout.strip()
    assert len(tid) == 12
    p = _cli("stop", tid)  # may already be done; both fine
    assert p.returncode == 0
    p = _cli("status", "nosuchid")
    assert p.returncode == 1
    p = _cli("list")
    assert p.returncode == 0
    json.loads(p.stdout)
