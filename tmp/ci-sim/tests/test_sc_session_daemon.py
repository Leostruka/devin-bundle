"""sc_sessions daemon -- pidfile, auth envelope, malformed input, reaping."""
import json
import os
import socket
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_sessions  # noqa: E402

PY = sys.executable


@pytest.fixture
def daemon(tmp_path, monkeypatch):
    pf = str(tmp_path / "pidfile.json")
    monkeypatch.setattr(sc_sessions, "PIDFILE", pf)
    monkeypatch.setattr(sc_sessions, "IDLE_TTL_S", 120)
    yield pf
    sc_sessions.stop_daemon()


def _rpc_raw(port, payload):
    s = socket.create_connection(("127.0.0.1", port), timeout=10)
    with s:
        s.sendall(payload)
        data = b""
        while not data.endswith(b"\n"):
            chunk = s.recv(1 << 20)
            if not chunk:
                break
            data += chunk
    return json.loads(data.decode())


def _pidfile(pf):
    with open(pf, encoding="utf-8") as f:
        return json.load(f)


def test_start_daemon_writes_pidfile(daemon):
    r = sc_sessions.start_daemon()
    assert r["ok"] and r["daemon"]["pid"] > 0
    d = _pidfile(daemon)
    assert d["pid"] == r["daemon"]["pid"]
    assert d["port"] == r["daemon"]["port"]
    assert d["generation"] == r["daemon"]["generation"]
    assert len(d["daemon_token"]) == 32


def test_start_daemon_idempotent(daemon):
    r1 = sc_sessions.start_daemon()
    r2 = sc_sessions.start_daemon()
    assert r1["ok"] and r2["ok"]
    assert r2["daemon"]["pid"] == r1["daemon"]["pid"]


def test_daemon_status_running(daemon):
    assert sc_sessions.daemon_status()["running"] is False
    sc_sessions.start_daemon()
    st = sc_sessions.daemon_status()
    assert st["ok"] and st["running"] is True
    assert st["generation"]
    assert st["sessions"] == 0


def test_stop_daemon_missing_ok(daemon):
    r = sc_sessions.stop_daemon()
    assert r["ok"] is True and r["running"] is False


def test_stop_daemon_removes_pidfile(daemon):
    sc_sessions.start_daemon()
    d = _pidfile(daemon)
    r = sc_sessions.stop_daemon()
    assert r["ok"] is True
    deadline = time.time() + 10
    while time.time() < deadline:
        if not sc_sessions._pid_alive(d["pid"]):
            break
        time.sleep(0.1)
    else:
        pytest.fail("daemon still alive")
    assert not os.path.exists(daemon)


def test_stale_pidfile_removed_not_attached(daemon):
    # Dead pid + unreachable port: never silently attached.
    with open(daemon, "w", encoding="utf-8") as f:
        json.dump({"pid": 99999999, "port": 1,
                   "generation": "x" * 32, "daemon_token": "y" * 32,
                   "started": time.time()}, f)
    r = sc_sessions.start_daemon()
    assert r["ok"] and r["daemon"]["pid"] != 99999999
    assert _pidfile(daemon)["generation"] != "x" * 32


def test_ping_needs_no_token(daemon):
    sc_sessions.start_daemon()
    d = _pidfile(daemon)
    r = _rpc_raw(d["port"],
                 json.dumps({"op": "ping"}).encode() + b"\n")
    assert r["ok"] is True and r["generation"] == d["generation"]


def test_foreign_token_rejected_before_dispatch(daemon):
    sc_sessions.start_daemon()
    d = _pidfile(daemon)
    for env in (
            {"op": "list"},
            {"op": "list", "daemon_token": "0" * 32,
             "generation": d["generation"]},
            {"op": "list", "daemon_token": d["daemon_token"],
             "generation": "f" * 32},
            {"op": "spawn", "daemon_token": "0" * 32,
             "generation": "f" * 32,
             "arg": {"argv": [PY, "-c", "pass"]}}):
        r = _rpc_raw(d["port"], json.dumps(env).encode() + b"\n")
        assert r["ok"] is False and r["status"] == "rejected", env


def test_malformed_message_structured_error(daemon):
    sc_sessions.start_daemon()
    d = _pidfile(daemon)
    r = _rpc_raw(d["port"], b"this is not json\n")
    assert r["ok"] is False and r["error"]
    r = _rpc_raw(d["port"],
                 json.dumps({"op": "ping"}).encode() + b"\n")
    assert r["ok"] is True


def test_oversized_line_structured_error(daemon):
    sc_sessions.start_daemon()
    d = _pidfile(daemon)
    s = socket.create_connection(("127.0.0.1", d["port"]), timeout=10)
    with s:
        s.sendall(b"x" * (sc_sessions.MAX_LINE + 1))
        data = b""
        while not data.endswith(b"\n"):
            chunk = s.recv(1 << 20)
            if not chunk:
                break
            data += chunk
    r = json.loads(data.decode())
    assert r["ok"] is False and r["error"]


def test_daemon_stop_reaps_children(daemon):
    sc_sessions.start_daemon()
    r = sc_sessions.spawn_session(
        [PY, "-u", "-c", "import time;time.sleep(60)"])
    assert r["ok"]
    pid = r["session"]["pid"]
    sc_sessions.stop_daemon()
    deadline = time.time() + 15
    while time.time() < deadline:
        if not sc_sessions._pid_alive(pid):
            break
        time.sleep(0.1)
    else:
        pytest.fail("session child survived daemon stop")


def test_idle_ttl_exit(daemon, monkeypatch):
    monkeypatch.setattr(sc_sessions, "IDLE_TTL_S", 2)
    r = sc_sessions.start_daemon()
    pid = r["daemon"]["pid"]
    deadline = time.time() + 15
    while time.time() < deadline:
        if not sc_sessions._pid_alive(pid):
            break
        time.sleep(0.2)
    else:
        pytest.fail("daemon did not idle-exit")
    assert not os.path.exists(daemon)


def test_stale_generation_rejected_without_socket(daemon, monkeypatch):
    sc_sessions.start_daemon()
    r = sc_sessions.spawn_session(
        [PY, "-u", "-c", "import time;time.sleep(60)"])
    assert r["ok"]
    sess = r["session"]
    # Restart the daemon: pidfile now names a new generation.
    sc_sessions.stop_daemon()
    sc_sessions.start_daemon()
    calls = []

    def boom(*a, **k):
        calls.append(a)
        raise AssertionError("socket must not be opened")

    monkeypatch.setattr(socket, "create_connection", boom)
    for fn in (lambda: sc_sessions.recv(sess, timeout_s=1),
               lambda: sc_sessions.send(sess, "x\n"),
               lambda: sc_sessions.close(sess),
               lambda: sc_sessions.cancel(sess),
               lambda: sc_sessions.resize(sess, 80, 24)):
        res = fn()
        assert res["ok"] is False
        assert res["status"] == "rejected"
        assert res["error"] == "stale daemon generation"
    assert calls == []


def test_live_pidfile_ping_timeout_never_respawns(daemon, monkeypatch):
    r = sc_sessions.start_daemon()
    d = _pidfile(daemon)
    monkeypatch.setattr(
        sc_sessions, "_rpc",
        lambda *a, **k: {"ok": False, "error": "timeout"})
    r2 = sc_sessions.start_daemon()
    assert r2["ok"] is False and "unresponsive" in r2["error"]
    assert os.path.exists(daemon)
    assert _pidfile(daemon)["pid"] == d["pid"]


def test_stop_daemon_alive_unreachable_reports_running(daemon,
                                                       monkeypatch):
    sc_sessions.start_daemon()
    d = _pidfile(daemon)
    monkeypatch.setattr(
        sc_sessions, "_rpc",
        lambda *a, **k: {"ok": False, "error": "conn refused"})
    r = sc_sessions.stop_daemon()
    assert r["ok"] is False and r["running"] is True
    assert r["stopped"] is False
    assert os.path.exists(daemon)  # pidfile left intact
    monkeypatch.undo()
    sc_sessions.stop_daemon()


def test_pidfile_atomic_write_roundtrip(daemon):
    sc_sessions.start_daemon()
    d = _pidfile(daemon)
    assert d["pid"] > 0 and d["port"] > 0
    leftovers = [f for f in os.listdir(os.path.dirname(daemon))
                 if f.endswith(".tmp")]
    assert leftovers == []
