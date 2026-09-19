"""Spawn mode — fake pywinpty PTY behind _pty_factory seam; registry file."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


class FakePTY:
    def __init__(self, shell, dims):
        self.shell = shell
        self.dims = dims
        self.writes = []
        self.alive = True
        self.feed = ""
        self.resized = []

    def read(self):
        d, self.feed = self.feed, ""
        return d

    def write(self, text):
        self.writes.append(text)

    def isalive(self):
        return self.alive

    def set_size(self, rows, cols):
        self.resized.append((rows, cols))

    def terminate(self):
        self.alive = False


@pytest.fixture
def fakes(tmp_path, monkeypatch):
    made = {}

    def factory(shell, cols, rows):
        p = FakePTY(shell, (rows, cols))
        made[id(p)] = p
        return p

    monkeypatch.setattr(t, "_pty_factory", factory)
    monkeypatch.setattr(t, "_SESSIONS_OVERRIDE",
                        str(tmp_path / "tsessions.json"))
    return made


def test_spawn_registers_session(fakes):
    r = t.spawn(shell="cmd", cols=120, rows=30)
    assert r["ok"] is True
    sid = r["session"]
    assert t.sessions()[sid]["shell"] == "cmd"


def test_spawn_bad_shell(fakes):
    assert t.spawn(shell="csh")["ok"] is False


def test_send_to_writes(fakes):
    sid = t.spawn()["session"]
    t.send_to(sid, "echo hi\r\n")
    p = next(iter(fakes.values()))
    assert p.writes == ["echo hi\r\n"]


def test_recv_collects(fakes):
    sid = t.spawn()["session"]
    p = next(iter(fakes.values()))
    p.feed = "banner stuff"
    out = t.recv_from(sid)
    assert "banner stuff" in out["output"]


def test_recv_wait_regex(fakes):
    sid = t.spawn()["session"]
    p = next(iter(fakes.values()))
    p.feed = "abc MARKER xyz"
    out = t.recv_from(sid, wait="MARKER", timeout=1.0)
    assert out["ok"] is True
    assert "MARKER" in out["output"]


def test_recv_wait_timeout(fakes):
    sid = t.spawn()["session"]
    out = t.recv_from(sid, wait="NEVER", timeout=0.3)
    assert out["ok"] is False
    assert "timeout" in out["error"]


def test_close_session(fakes):
    sid = t.spawn()["session"]
    assert t.close_session(sid)["ok"] is True
    assert sid not in t.sessions()


def test_kill_terminates(fakes):
    sid = t.spawn()["session"]
    p = next(iter(fakes.values()))
    t.kill(sid)
    assert p.alive is False


def test_send_unknown_session(fakes):
    assert t.send_to("nope", "x")["ok"] is False
