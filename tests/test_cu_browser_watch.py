"""browser.py watch: CDP screencast -> jpeg frames on disk."""
import base64, io, json, os, sys
from contextlib import redirect_stdout
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

br = cu_load.load("cu_browser")
cli_mod = cu_load.load("browser")

FRAME = base64.b64encode(b"\xff\xd8fakejpeg").decode()


class FakeWS:
    def __init__(self, frames):
        import collections
        self.dialect = "cdp"
        self.events = collections.deque(frames)
        self.sent = []

    def call(self, method, params=None, timeout=None):
        self.sent.append((method, params))
        return {}

    def start_reader(self):
        pass

    def close(self):
        pass


class FakeCli:
    def __init__(self, ws, dialect="cdp"):
        self._ws = ws
        self.dialect = dialect
        self.endpoint = "x"


def _frame(i):
    return {"method": "Page.screencastFrame",
            "params": {"data": FRAME, "sessionId": i,
                       "metadata": {"deviceWidth": 10,
                                    "deviceHeight": 10}}}


def test_watch_writes_frames_and_acks(monkeypatch, tmp_path):
    ws = FakeWS([_frame(1), _frame(2)])
    cli = FakeCli(ws)
    r = br.watch_frames(cli, seconds=0.1, out_dir=str(tmp_path))
    assert r["ok"] and r["frames"] == 2
    assert os.path.isfile(tmp_path / "frame-0001.jpg")
    acks = [m for m, p in ws.sent if m == "Page.screencastFrameAck"]
    assert len(acks) == 2
    sent_methods = [m for m, _ in ws.sent]
    assert "Page.startScreencast" in sent_methods
    assert "Page.stopScreencast" in sent_methods


def test_watch_rejects_bidi(tmp_path):
    cli = FakeCli(FakeWS([]), dialect="bidi")
    r = br.watch_frames(cli, seconds=0.1, out_dir=str(tmp_path))
    assert r["ok"] is False and r["error"] == "screencast_cdp_only"


def test_watch_last_only(tmp_path):
    ws = FakeWS([_frame(1), _frame(2)])
    r = br.watch_frames(FakeCli(ws), seconds=0.1,
                        out_dir=str(tmp_path), last_only=True)
    assert r["ok"] and os.path.isfile(tmp_path / "latest.jpg")
    assert not os.path.isfile(tmp_path / "frame-0001.jpg")
