"""terminal.py CLI — argv dispatch → cu_terminal ops; JSON out; no real OS."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")
cli_mod = cu_load.load("terminal")


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(t, "_BINDING_OVERRIDE", str(tmp_path / "b.json"))
    monkeypatch.setattr(cu_load.sys.modules["cu_hints"], "session_id",
                        lambda: "sess-test")
    yield


def _run(argv, capsys):
    old = sys.argv
    sys.argv = ["terminal.py"] + argv
    try:
        try:
            cli_mod.main()
        except SystemExit:
            pass
    finally:
        sys.argv = old
    out = capsys.readouterr().out.strip()
    return json.loads(out) if out else {}


def test_cli_bind(capsys):
    r = _run(["bind", "--hwnd", "10"], capsys)
    assert r["ok"] is False or "error" in r or r.get("bound") is not None


def test_cli_status_unbound(capsys):
    r = _run(["status"], capsys)
    assert r["ok"] is True and r["bound"] is False


def test_cli_read_needs_binding(capsys, monkeypatch):
    r = _run(["read"], capsys)
    assert r["ok"] is False
    assert "binding" in r["error"].lower() or "bind" in r["error"].lower()


def test_cli_type_needs_binding(capsys):
    r = _run(["type", "hello"], capsys)
    assert r["ok"] is False


def test_cli_unbind(capsys):
    r = _run(["unbind"], capsys)
    assert r["ok"] is True


def test_cli_sessions_status_no_daemon(capsys, monkeypatch):
    monkeypatch.setattr(cli_mod, "_daemon_info", lambda: None)
    r = _run(["sessions", "status"], capsys)
    assert r["ok"] is False
    assert "daemon" in r["error"]


def test_cli_spawn_routes_to_daemon(capsys, monkeypatch):
    calls = []

    def fake_call(op, arg=None):
        calls.append((op, arg))
        return {"ok": True, "sid": "s1"}

    monkeypatch.setattr(cli_mod, "_daemon_info",
                        lambda: {"pid": 1, "port": 1, "session": "x"})
    monkeypatch.setattr(cli_mod, "_daemon_call", fake_call)
    r = _run(["spawn", "--shell", "cmd"], capsys)
    assert r == {"ok": True, "sid": "s1"}
    assert calls == [("spawn", {"shell": "cmd", "cols": 120, "rows": 30})]


def test_cli_recv_routes_to_daemon(capsys, monkeypatch):
    calls = []

    def fake_call(op, arg=None):
        calls.append((op, arg))
        return {"ok": True, "output": "x"}

    monkeypatch.setattr(cli_mod, "_daemon_info",
                        lambda: {"pid": 1, "port": 1, "session": "x"})
    monkeypatch.setattr(cli_mod, "_daemon_call", fake_call)
    r = _run(["recv", "s1", "--tail", "5", "--wait", "done"], capsys)
    assert r["ok"] is True
    assert calls == [("recv", {"sid": "s1", "tail": 5, "wait": "done",
                              "timeout": 10.0})]


def test_cli_kill_routes_to_daemon(capsys, monkeypatch):
    monkeypatch.setattr(cli_mod, "_daemon_info",
                        lambda: {"pid": 1, "port": 1, "session": "x"})
    seen = []
    monkeypatch.setattr(cli_mod, "_daemon_call",
                        lambda op, arg=None: seen.append(op) or {"ok": True})
    r = _run(["kill", "s1"], capsys)
    assert r["ok"] is True and seen == ["kill"]
