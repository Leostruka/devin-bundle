"""browser.py CLI gates: argv dispatch → JSON stdout, client unavailable is a
typed error, events daemon absent is a typed error."""
import io
import json
import os
import sys
from contextlib import redirect_stdout

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

hints = cu_load.load("cu_hints")
br = cu_load.load("cu_browser")
cli_mod = cu_load.load("browser")


class FakeClient:
    dialect = "cdp"
    endpoint = "http://127.0.0.1:9222"

    def __init__(self):
        self.eval_queue = []
        self.calls = []

    def evaluate(self, expr):
        self.calls.append(("eval", expr))
        return self.eval_queue.pop(0) if self.eval_queue else None

    def install_collector(self):
        self.calls.append(("install", None))
        return {"ok": True, "installed": "installed"}

    def collector(self, kind, clear=False):
        self.calls.append(("collector", (kind, clear)))
        return [{"level": "warn", "text": "hi"}]

    def wait(self, **kw):
        self.calls.append(("wait", kw))
        return {"ok": True, "matched": "x"}

    def cookies(self):
        return [{"name": "a"}]

    def storage(self, area, op, key=None, value=None):
        return [("k", "v")]

    def find(self, kind, value, name=None):
        return [{"tag": "BUTTON", "bounds": [0, 0, 1, 1]}]

    def tabs(self):
        return [{"id": "p1", "title": "A"}]

    def navigate(self, url):
        self.calls.append(("nav", url))
        return {"frameId": "f"}

    def close(self):
        pass


@pytest.fixture
def client(monkeypatch):
    c = FakeClient()
    monkeypatch.setattr(br, "_cdp_client", lambda timeout=10.0: c)
    return c


def run(argv):
    old = sys.argv
    sys.argv = ["browser.py"] + argv
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            cli_mod.main()
    except SystemExit:
        pass
    finally:
        sys.argv = old
    return json.loads(buf.getvalue().strip())


def test_eval_returns_result(client):
    client.eval_queue = [42]
    out = run(["eval", "1+1"])
    assert out == {"ok": True, "result": 42}


def test_eval_boundaries_wraps_strings(client):
    client.eval_queue = ["page text"]
    out = run(["eval", "document.title", "--boundaries"])
    assert out["bounded"] is True
    assert "UNTRUSTED" in out["result"]


def test_console_auto_installs_and_filters(client):
    # first evaluate: collector missing; collector(): items
    client.eval_queue = [False]
    out = run(["console", "--substr", "warn"])
    assert ("install", None) in client.calls
    assert out["count"] == 1 and out["items"][0]["text"] == "hi"


def test_console_clear_drains(client):
    client.eval_queue = [True]
    run(["console", "--clear"])
    assert ("collector", ("log", True)) in client.calls


def test_wait_passes_conditions(client):
    out = run(["wait", "--selector", "#x", "--timeout", "3"])
    assert out["ok"] is True
    kind, kw = client.calls[-1]
    assert kind == "wait" and kw["selector"] == "#x" and kw["timeout"] == 3.0


def test_tabs(client):
    assert run(["tabs"])["tabs"][0]["id"] == "p1"


def test_find(client):
    out = run(["find", "role", "button", "--name", "Go"])
    assert out["elements"][0]["tag"] == "BUTTON"


def test_unavailable_is_typed_error(monkeypatch):
    monkeypatch.setattr(br, "_cdp_client", lambda timeout=10.0: None)
    out = run(["eval", "1"])
    assert out["ok"] is False and "browser_unavailable" in out["error"]


def test_events_without_daemon_is_typed_error(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_mod, "EVENTS_PATH", str(tmp_path / "ev.json"))
    out = run(["events", "drain"])
    assert out["ok"] is False and "not running" in out["error"]


def test_events_call_sends_op(tmp_path, monkeypatch):
    """events subcommands forward {op} to the daemon socket."""
    import socket
    import threading
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    got = {}

    def serve():
        conn, _ = srv.accept()
        data = conn.recv(65536)
        got.update(json.loads(data.decode().strip()))
        conn.sendall(b'{"ok": true, "events": []}\n')
        conn.close()
        srv.close()

    threading.Thread(target=serve, daemon=True).start()
    pf = tmp_path / "ev.json"
    pf.write_text(json.dumps({"pid": os.getpid(), "port": port,
                              "session": "s1"}))
    monkeypatch.setattr(cli_mod, "EVENTS_PATH", str(pf))
    monkeypatch.setattr(cli_mod, "_events_info", lambda: {
        "pid": os.getpid(), "port": port, "session": "s1"})
    out = run(["events", "drain"])
    assert out["ok"] is True
    assert got["op"]["op"] == "drain" and got["session"] == "s1"
