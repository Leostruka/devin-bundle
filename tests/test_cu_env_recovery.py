"""Gate for C08: cancel & recovery on the remote path.

- may_retry: only provably-side-effect-free results retry
- request IDs deduped at the daemon — an uncertain request NEVER replays
- heartbeat staleness -> env_not_ready (dead daemon, not silent hang)
- cleanup: remote releases via backend, never cu_actions.emergency_release
- a cancelled queue never executes after reconnect
"""
import json
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_backend = load("cu_backend")
cu_qmp_backend = load("cu_qmp_backend")
cu_env_daemon = load("cu_env_daemon")


# --- may_retry --------------------------------------------------------------------

def test_ambiguous_action_is_not_retryable():
    assert cu_backend.may_retry(
        {"status": "unknown", "dispatch": {"sent": None}}) is False


@pytest.mark.parametrize("status", ["dispatched", "unknown", "timeout",
                                    "error"])
def test_side_effect_results_never_retry(status):
    assert cu_backend.may_retry({"ok": True, "status": status}) is False


def test_pre_send_rejection_is_retryable():
    assert cu_backend.may_retry({"ok": False,
                                 "status": "rejected"}) is True
    assert cu_backend.may_retry({"ok": True,
                                 "status": "dry_run"}) is True


def test_read_only_query_may_retry():
    assert cu_backend.may_retry({"ok": True, "status": "dispatched",
                                 "read_only": True}) is True


# --- daemon journal / dedup --------------------------------------------------------

def test_duplicate_completed_request_returns_cached(tmp_path):
    """Same request_id twice -> QEMU sees it ONCE, second response is
    the cached result."""
    d = tmp_path / "env"
    d.mkdir()
    j = cu_env_daemon.Journal(d / "requests.jsonl")

    calls = []

    def exec_once(cmd, args):
        calls.append(cmd)
        return {"ok": True, "return": {"x": 1}}

    r1 = j.execute("rid-1", "query-status", None, exec_once)
    r2 = j.execute("rid-1", "query-status", None, exec_once)
    assert r1 == r2
    assert calls == ["query-status"]


def test_uncertain_request_never_replays(tmp_path):
    """accepted-but-never-completed (daemon died mid-call): a retry of
    the same request_id must NOT re-execute the op."""
    d = tmp_path / "env"
    d.mkdir()
    j = cu_env_daemon.Journal(d / "requests.jsonl")
    j.begin("rid-9", "input-send-event")  # accepted, never completes

    calls = []

    def must_not_run(cmd, args):
        calls.append(cmd)
        return {"ok": True, "return": {}}

    j2 = cu_env_daemon.Journal(d / "requests.jsonl")  # fresh instance
    r = j2.execute("rid-9", "input-send-event", None, must_not_run)
    assert calls == []
    assert r["ok"] is False
    assert "request_uncertain" in r["error"]


# --- backend: uncertain sends, heartbeat ------------------------------------------

@pytest.fixture
def env_dir(tmp_path):
    d = tmp_path / "devin-linux"
    d.mkdir()
    (d / "ready.json").write_text(json.dumps({
        "socket": "tcp://127.0.0.1:1", "token": "t0k",
        "qemu_pid": 1, "daemon_pid": 2}))
    return d


def test_uncertain_send_is_typed(env_dir):
    """ACK lost after the request left the pipe -> outcome is
    unknowable; typed 'uncertain', never retryable."""
    def die(sock, msg, timeout_s, token=None):
        raise TimeoutError("ack lost")

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=die)
    with pytest.raises(cu_qmp_backend.BackendError, match="uncertain"):
        be.send_events(cu_qmp_backend.encode_key("enter"))


def test_every_call_carries_request_id(env_dir):
    sent = []

    def ipc(sock, msg, timeout_s, token=None):
        sent.append(msg)
        return {"ok": True, "return": {}}

    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    be.send_events(cu_qmp_backend.encode_key("enter"))
    be.status()
    assert all("request_id" in m for m in sent)
    assert len({m["request_id"] for m in sent}) == 2


def test_stale_heartbeat_is_not_ready(env_dir):
    (env_dir / "hb").write_text(str(time.time() - 60))
    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=lambda *a, **k: None)
    with pytest.raises(cu_qmp_backend.BackendError,
                       match="heartbeat"):
        be.status()


def test_fresh_heartbeat_passes(env_dir):
    (env_dir / "hb").write_text(str(time.time()))
    be = cu_qmp_backend.QmpBackend(
        "devin-linux", env_dir=env_dir,
        ipc=lambda *a, **k: {"ok": True, "return": {"running": True}})
    assert be.status()["running"] is True


# --- cleanup: remote never touches host input -------------------------------------

def test_remote_cleanup_uses_backend_not_host(env_dir, monkeypatch):
    """cu_backend.cleanup on a remote target must never run
    cu_actions.emergency_release — that releases HOST input state."""
    import cu_actions
    monkeypatch.setattr(cu_actions, "emergency_release",
                        lambda: pytest.fail("host release on remote"))

    calls = []

    def ipc(sock, msg, timeout_s, token=None):
        calls.append(msg)
        return {"ok": True, "return": {}}

    target = {"kind": "qemu", "env_id": "devin-linux"}
    be = cu_qmp_backend.QmpBackend("devin-linux", env_dir=env_dir,
                                 ipc=ipc)
    monkeypatch.setattr(cu_backend, "open_backend",
                        lambda t: be)
    cu_backend.cleanup(target)
    assert calls and calls[0]["command"] == "release-all"


# --- cancelled queue never fires ---------------------------------------------------

def test_partial_request_on_dead_connection_never_executes(tmp_path):
    """EOF mid-line: the daemon discards the incomplete request — a
    reconnect must not find it half-executed."""
    class DeadConn:
        def __init__(self):
            self.sent = False

        def recv(self, n):
            if self.sent:
                return b""  # EOF after the partial line
            self.sent = True
            return b'{"command": "quit"'  # no newline -> incomplete

    conn = DeadConn()
    assert cu_env_daemon._read_request(conn) is None
