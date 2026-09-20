"""sc_sessions client surface -- spawn/send/recv/close/cancel lifecycle."""
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_cli  # noqa: E402
import sc_policy  # noqa: E402
import sc_sessions  # noqa: E402

PY = sys.executable

ECHO = ("import sys\n"
        "sys.stdout.write('READY\\n');sys.stdout.flush()\n"
        "for line in sys.stdin:\n"
        "    sys.stdout.write('ECHO:' + line);sys.stdout.flush()")


def py(code):
    return [PY, "-u", "-c", code]


@pytest.fixture
def daemon(tmp_path, monkeypatch):
    monkeypatch.setattr(sc_sessions, "PIDFILE",
                        str(tmp_path / "pidfile.json"))
    monkeypatch.setattr(sc_sessions, "IDLE_TTL_S", 120)
    yield
    sc_sessions.stop_daemon()


def _wait_text(session, needle, timeout=15):
    deadline = time.time() + timeout
    cursor = None
    while time.time() < deadline:
        r = sc_sessions.recv(session, cursor=cursor, timeout_s=1)
        assert r["ok"]
        cursor = r["cursor"]
        if needle in "".join(x["text"] for x in r["records"]):
            return r
        time.sleep(0.05)
    pytest.fail(f"never saw {needle!r}")


def _spawn_ready(child=None, **kw):
    r = sc_sessions.spawn_session(py(child if child else ECHO), **kw)
    assert r["ok"], r
    s = r["session"]
    _wait_text(s, "READY")
    return s


def test_spawn_session_shape(daemon):
    s = _spawn_ready()
    for key in ("id", "token", "generation", "daemon_token", "pid",
                "start_time", "argv", "cwd", "capacity", "created_at"):
        assert key in s, key
    assert s["pid"] > 0 and s["capacity"] == 2048
    json.dumps(s)
    sc_sessions.close(s)


def test_send_recv_echo_roundtrip(daemon):
    s = _spawn_ready()
    r = sc_sessions.send(s, "hello\n")
    assert r["ok"] and r["delivered"] == len("hello\n".encode())
    r = _wait_text(s, "ECHO:hello")
    assert r["records"][-1]["seq"] > 0
    sc_sessions.close(s)


def test_ring_overflow_reports_dropped(daemon):
    code = ("import sys\n"
            "sys.stdout.write('READY\\n');sys.stdout.flush()\n"
            "import time\n"
            "for i in range(10):\n"
            "    sys.stdout.write('line%d\\n' % i)\n"
            "    sys.stdout.flush();time.sleep(0.15)\n"
            "time.sleep(30)")
    s = _spawn_ready(code, capacity=4)
    deadline = time.time() + 15
    r = {}
    while time.time() < deadline:
        r = sc_sessions.recv(s, timeout_s=1)
        if r["dropped"] >= 6:
            break
        time.sleep(0.1)
    assert r["dropped"] >= 6
    assert len(r["records"]) <= 4
    sc_sessions.close(s)


def test_recv_cursor_paging(daemon):
    s = _spawn_ready()
    r1 = sc_sessions.recv(s, timeout_s=1)
    assert r1["ok"] and "READY" in r1["records"][0]["text"]
    cur = r1["cursor"]
    sc_sessions.send(s, "one\n")
    _wait_text(s, "ECHO:one")
    r2 = sc_sessions.recv(s, cursor=cur, timeout_s=1)
    texts = "".join(x["text"] for x in r2["records"])
    assert "READY" not in texts and "ECHO:one" in texts
    r3 = sc_sessions.recv(s, cursor=r2["cursor"], timeout_s=1)
    assert all(x["seq"] > r2["cursor"] for x in r3["records"])
    sc_sessions.close(s)


def test_recv_tail(daemon):
    s = _spawn_ready()
    sc_sessions.send(s, "a\n")
    _wait_text(s, "ECHO:a")
    r = sc_sessions.recv(s, tail=1, timeout_s=1)
    assert len(r["records"]) == 1 and "ECHO:a" in r["records"][0]["text"]
    sc_sessions.close(s)


def test_recv_wait_regex_hit(daemon):
    s = _spawn_ready()
    r = sc_sessions.recv(s, cursor=0, wait=r"READY", timeout_s=5)
    assert r["ok"] and r["matched"] is True
    sc_sessions.close(s)


def test_recv_wait_regex_timeout(daemon):
    s = _spawn_ready()
    t0 = time.time()
    r = sc_sessions.recv(s, cursor=0, wait=r"NEVER_MATCHES",
                         timeout_s=1)
    assert time.time() - t0 >= 0.8
    assert r["ok"] and r["matched"] is False
    sc_sessions.close(s)


def test_recv_bad_regex_rejected(daemon):
    s = _spawn_ready()
    r = sc_sessions.recv(s, wait="(", timeout_s=1)
    assert r["ok"] is False
    sc_sessions.close(s)


def test_resize_unsupported(daemon):
    s = _spawn_ready()
    r = sc_sessions.resize(s, 120, 40)
    assert r["ok"] is False
    assert "unsupported" in r["error"]
    sc_sessions.close(s)


def test_send_validates_data(daemon):
    s = _spawn_ready()
    for bad in ("", 123, b"x", None):
        r = sc_sessions.send(s, bad)
        assert r["ok"] is False, bad
    sc_sessions.close(s)


def test_send_to_exited_session(daemon):
    r = sc_sessions.spawn_session(py("print('READY')"))
    s = r["session"]
    deadline = time.time() + 10
    rr = {}
    while time.time() < deadline:
        rr = sc_sessions.recv(s, timeout_s=1)
        if rr["exited"]:
            break
        time.sleep(0.1)
    assert rr["exited"] and rr["exit_code"] == 0
    r = sc_sessions.send(s, "x\n")
    assert r["ok"] is False and "exited" in r["error"]
    sc_sessions.close(s)


def test_close_kills_tree(daemon):
    s = _spawn_ready()
    r = sc_sessions.close(s)
    assert r["ok"]
    pid = s["pid"]
    deadline = time.time() + 10
    while time.time() < deadline:
        if not sc_sessions._pid_alive(pid):
            break
        time.sleep(0.1)
    else:
        pytest.fail("child still alive after close")
    r = sc_sessions.recv(s, timeout_s=1)
    assert r["ok"] is False and r["status"] == "rejected"


def test_cancel_keeps_buffer(daemon):
    s = _spawn_ready()
    sc_sessions.send(s, "buf\n")
    _wait_text(s, "ECHO:buf")
    r = sc_sessions.cancel(s)
    assert r["ok"]
    pid = s["pid"]
    deadline = time.time() + 10
    while time.time() < deadline:
        if not sc_sessions._pid_alive(pid):
            break
        time.sleep(0.1)
    r = sc_sessions.recv(s, timeout_s=1)
    assert r["ok"] and "ECHO:buf" in "".join(
        x["text"] for x in r["records"])
    assert r["exited"] is True
    sc_sessions.close(s)


def test_stale_session_dict_rejected(daemon):
    s = _spawn_ready()
    for bad in ({}, {"id": s["id"]},
                {**s, "token": "0" * 32},
                {**s, "generation": "f" * 32},
                {**s, "daemon_token": "f" * 32}):
        r = sc_sessions.recv(bad, timeout_s=1)
        assert r["ok"] is False, bad
        assert r.get("status") == "rejected" or "error" in r
    sc_sessions.close(s)


def test_recv_limit(daemon):
    code = ("import sys\n"
            "sys.stdout.write('READY\\n');sys.stdout.flush()\n"
            "import time\n"
            "for i in range(5):\n"
            "    sys.stdout.write('x%d\\n' % i);sys.stdout.flush()\n"
            "    time.sleep(0.15)\n"
            "time.sleep(30)")
    s = _spawn_ready(code)
    deadline = time.time() + 15
    r = {}
    while time.time() < deadline:
        r = sc_sessions.recv(s, limit=3, timeout_s=1)
        if r["cursor"] >= 6:
            break
        time.sleep(0.1)
    assert len(r["records"]) == 3
    sc_sessions.close(s)


# --- CLI arg validation -------------------------------------------------

def _run(argv, capsys):
    code = sc_cli.main(argv)
    out = capsys.readouterr().out.strip()
    return code, json.loads(out)


def test_cli_sessions_start_status_stop(capsys, daemon, tmp_path,
                                        monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "conf")
    code, r = _run(["sessions", "start"], capsys)
    assert code == 0 and r["ok"]
    code, r = _run(["sessions", "status"], capsys)
    assert code == 0 and r["value"]["running"] is True
    code, r = _run(["sessions", "list"], capsys)
    assert code == 0 and r["value"]["sessions"] == []
    code, r = _run(["sessions", "stop"], capsys)
    assert code == 2 and r["status"] == "rejected"  # needs confirmation


def test_cli_session_spawn_requires_confirmation(capsys, daemon):
    code, r = _run(["session", "spawn", "--", PY, "-c", "pass"],
                   capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_session_bad_session_file_rejected(capsys, daemon,
                                               tmp_path):
    for argv in (
            ["session", "recv", "--session-file",
             str(tmp_path / "missing.json")],
            ["session", "close", "--session-file",
             str(tmp_path / "missing.json")],
            ["session", "send", "--session-file",
             str(tmp_path / "missing.json"), "--data", "x",
             "--confirmation-id", "c" * 64]):
        code, r = _run(argv, capsys)
        assert code == 2 and r["status"] == "rejected", argv


def test_cli_session_spawn_send_recv_flow(capsys, daemon, tmp_path,
                                          monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "conf")
    argv = py(ECHO)
    req = {"version": 1, "request_id": "sp1",
           "capability": "session.spawn",
           "args": {"argv": argv, "cwd": None, "capacity": 2048,
                    "idle_ttl_s": 900},
           "deadline_ms": 30000, "policy": {"dry_run": False}}
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    sf = tmp_path / "sess.json"
    code, r = _run(["session", "spawn", "--request-id", "sp1",
                    "--confirmation-id", cid,
                    "--out-file", str(sf),
                    "--"] + argv, capsys)
    assert code == 0 and r["ok"], r
    assert sf.exists()
    _wait_text(json.loads(sf.read_text()), "READY")
    sess_id = json.loads(sf.read_text())["id"]
    req2 = {"version": 1, "request_id": "sd1",
            "capability": "session.send",
            "args": {"session_id": sess_id, "data": "hi\n"},
            "deadline_ms": 30000, "policy": {"dry_run": False}}
    cid2 = sc_policy.issue_confirmation(req2)["confirmation_id"]
    code, r = _run(["session", "send", "--request-id", "sd1",
                    "--session-file", str(sf), "--data", "hi\n",
                    "--confirmation-id", cid2], capsys)
    assert code == 0 and r["ok"], r
    s = json.loads(sf.read_text())
    _wait_text(s, "ECHO:hi")
    code, r = _run(["session", "recv", "--session-file", str(sf),
                    "--tail", "5"], capsys)
    assert code == 0 and r["ok"]
    code, r = _run(["session", "close", "--session-file", str(sf)],
                   capsys)
    assert code == 0 and r["ok"]


def test_send_oversized_rejected(daemon):
    s = _spawn_ready()
    r = sc_sessions.send(s, "x" * 70000)
    assert r["ok"] is False and r["status"] == "rejected"
    assert "too large" in r["error"]
    sc_sessions.close(s)


def test_spawn_bad_capacity_idle_ttl_rejected(daemon):
    for kw in ({"capacity": 0}, {"capacity": 1.5}, {"capacity": "x"},
               {"capacity": True}, {"capacity": 65537},
               {"idle_ttl_s": 0}, {"idle_ttl_s": "x"},
               {"idle_ttl_s": True}, {"idle_ttl_s": 86401}):
        r = sc_sessions.spawn_session(py("pass"), **kw)
        assert r["ok"] is False and r["status"] == "rejected", kw
