"""Held-out daemon recovery contracts; lead-owned."""
import importlib
import os
import signal
import sys
import time
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"
PY = sys.executable


def load(name):
    sys.path.insert(0, str(EXT))
    return importlib.import_module(name)


def idle_child():
    return [PY, "-c",
            "import sys,time;sys.stdout.write('READY\\n');"
            "sys.stdout.flush();"
            "while True: time.sleep(0.1)"]


def wait_dead(pid, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return True
        try:
            if os.name == "posix":
                os.waitpid(pid, os.WNOHANG)
        except OSError:
            pass
        time.sleep(0.1)
    return False


@pytest.fixture
def daemon(tmp_path, monkeypatch):
    sess = load("sc_sessions")
    monkeypatch.setattr(sess, "PIDFILE", tmp_path / "daemon.json")
    monkeypatch.setattr(sess, "IDLE_TTL_S", 120)
    sess.start_daemon()
    yield sess
    try:
        sess.stop_daemon()
    except Exception:
        pass


def test_restart_rejects_stale_generation(daemon):
    s = daemon.spawn_session(idle_child())["session"]
    old_session = dict(s)
    daemon.stop_daemon()
    daemon.start_daemon()
    r = daemon.send(old_session, "echo no\n")
    assert r["ok"] is False
    assert r["status"] == "rejected"


def test_hard_killed_daemon_leaves_no_children(daemon):
    s = daemon.spawn_session(idle_child())["session"]
    child_pid = s["pid"]
    daemon_pid = daemon.daemon_status()["daemon"]["pid"]
    if os.name == "nt":
        import subprocess
        subprocess.run(["taskkill", "/PID", str(daemon_pid), "/F"],
                       capture_output=True)
    else:
        os.kill(daemon_pid, signal.SIGKILL)
    assert wait_dead(child_pid)


def test_stale_pidfile_never_attaches(daemon):
    daemon.stop_daemon()
    fake = ('{"pid": 999999, "port": 1, "generation": "ghost",'
            ' "daemon_token": "x", "started": 0}')
    deadline = time.time() + 5
    while True:
        try:
            tmp = daemon.PIDFILE.with_suffix(".fake")
            tmp.write_text(fake)
            os.replace(tmp, daemon.PIDFILE)
            break
        except OSError:
            if time.time() >= deadline:
                raise
            time.sleep(0.1)
    st = daemon.daemon_status()
    assert st["ok"] is True
    assert st["running"] is False
    assert st["generation"] is None


def test_closed_session_token_cannot_be_reused(daemon):
    s = daemon.spawn_session(idle_child())["session"]
    daemon.close(s)
    r = daemon.recv(s)
    assert r["ok"] is False
    assert r["status"] == "rejected"
