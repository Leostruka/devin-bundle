"""Tier 2 gates: _WSClient event capture + reader mode, browser_events
EventBuffer classification (console/errors/requests/dialogs/nav), dialog
auto-policy, drain semantics. No real browser — faked ws frames."""
import json
import os
import queue
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

hints = cu_load.load("cu_hints")
br = cu_load.load("cu_browser")
ev = cu_load.load("browser_events")


class ScriptedSock:
    """Fake websocket: recv pops scripted frames (or blocks on a queue)."""
    def __init__(self, frames=None):
        self.frames = list(frames or [])
        self.inbox = queue.Queue()
        self.sent = []

    def send(self, data):
        self.sent.append(json.loads(data))

    def recv(self):
        if self.frames:
            return json.dumps(self.frames.pop(0))
        item = self.inbox.get(timeout=5)
        if item is None:
            raise OSError("closed")
        return json.dumps(item)

    def close(self):
        self.inbox.put(None)
        # unblock waiters


def ws_client(frames, dialect="cdp", monkeypatch=None):
    """_WSClient whose websocket is a ScriptedSock — the `websocket`
    package isn't in the test env, so a fake module is injected."""
    import types
    sock = ScriptedSock(frames)
    fake_mod = types.ModuleType("websocket")
    fake_mod.create_connection = lambda *a, **k: sock
    monkeypatch.setitem(sys.modules, "websocket", fake_mod)
    c = br._WSClient("ws://x", dialect, timeout=3.0)
    return c, sock


# -- call() buffers skipped event frames ---------------------------------------

def test_call_buffers_event_frames(monkeypatch):
    c, sock = ws_client([], monkeypatch=monkeypatch)
    sock.inbox.put({"method": "Network.requestWillBeSent",
                    "params": {"requestId": "r1"}})
    sock.inbox.put({"id": 1, "result": {"ok": 1}})
    r = c.call("Runtime.evaluate", {"expression": "1"})
    assert r == {"ok": 1}
    assert len(c.events) == 1
    assert c.events[0]["method"] == "Network.requestWillBeSent"


def test_reader_mode_resolves_and_buffers(monkeypatch):
    c, sock = ws_client([], monkeypatch=monkeypatch)
    c.start_reader()
    try:
        sock.inbox.put({"method": "Runtime.consoleAPICalled",
                        "params": {"type": "log"}})
        # response must arrive AFTER call() registers its pending slot
        threading.Timer(0.05, lambda: sock.inbox.put(
            {"id": 1, "result": "ans"})).start()
        r = c.call("Runtime.evaluate", {"expression": "x"})
        assert r == "ans"
        time.sleep(0.2)
        methods = [e["method"] for e in c.events]
        assert "Runtime.consoleAPICalled" in methods
    finally:
        c.close()


def test_reader_eof_unblocks_pending(monkeypatch):
    c, sock = ws_client([], monkeypatch=monkeypatch)
    c.start_reader()
    sock.inbox.put(None)  # _recv_loop treats as EOF
    with pytest.raises(Exception):
        c.call("Runtime.evaluate", {"expression": "x"}, timeout=2.0)


# -- EventBuffer classification --------------------------------------------------

def cdp_buf():
    sock = ScriptedSock()
    ws = br._WSClient.__new__(br._WSClient)
    ws.dialect = "cdp"
    ws.timeout = 3.0
    ws.ws = sock
    ws._id = 0
    ws._eof = False
    import collections
    ws.events = collections.deque(maxlen=2000)
    ws._pending = {}
    ws._reader_t = None
    ws._send_lock = threading.Lock()
    return ev.EventBuffer(ws, "cdp"), sock


def push(buf, method, params):
    buf.ws.events.append({"method": method, "params": params})
    buf.pump()


def test_console_api_classified():
    buf, _ = cdp_buf()
    push(buf, "Runtime.consoleAPICalled",
         {"type": "warn", "args": [{"value": "careful"}],
          "timestamp": 1.0})
    d = buf.drain("console")
    assert d[0]["type"] == "warn"


def test_exception_classified_as_error():
    buf, _ = cdp_buf()
    push(buf, "Runtime.exceptionThrown",
         {"exceptionDetails": {"text": "boom",
                               "url": "http://x", "lineNumber": 3}})
    d = buf.drain("errors")
    assert d[0]["text"] == "boom"


def test_log_entry_classified():
    buf, _ = cdp_buf()
    push(buf, "Log.entryAdded",
         {"entry": {"source": "network", "level": "error",
                    "text": "404", "timestamp": 2}})
    d = buf.drain("console")
    assert d[0]["level"] == "error"


def test_network_request_lifecycle():
    buf, _ = cdp_buf()
    push(buf, "Network.requestWillBeSent",
         {"requestId": "r1", "request": {"url": "https://a/x",
                                         "method": "GET"},
          "type": "XHR", "timestamp": 1.0})
    push(buf, "Network.responseReceived",
         {"requestId": "r1", "response": {"status": 200,
                                          "mimeType": "application/json"},
          "timestamp": 1.5})
    push(buf, "Network.loadingFinished",
         {"requestId": "r1", "timestamp": 2.0})
    d = buf.drain("requests")
    assert len(d) == 1
    r = d[0]
    assert r["url"] == "https://a/x" and r["status"] == 200
    assert r["done"] is True and r["ms"] == pytest.approx(1000, rel=0.1)


def test_request_error_marked():
    buf, _ = cdp_buf()
    push(buf, "Network.requestWillBeSent",
         {"requestId": "r9", "request": {"url": "u", "method": "GET"},
          "timestamp": 1.0})
    push(buf, "Network.loadingFailed",
         {"requestId": "r9", "errorText": "net::ERR", "timestamp": 1.2})
    r = buf.drain("requests")[0]
    assert r["error"] == "net::ERR"


def test_dialog_auto_accept_alert():
    buf, sock = cdp_buf()
    sock.frames = [{"id": 1, "result": {}}]  # response for handler call
    push(buf, "Page.javascriptDialogOpening",
         {"type": "alert", "message": "hi"})
    sent = [f for f in sock.sent
            if f.get("method") == "Page.handleJavaScriptDialog"]
    assert sent and sent[0]["params"]["accept"] is True
    assert buf.drain("dialogs") == []  # nothing pending


def test_dialog_confirm_stays_pending():
    buf, _ = cdp_buf()
    push(buf, "Page.javascriptDialogOpening",
         {"type": "confirm", "message": "sure?"})
    d = buf.drain("dialogs")
    assert d[0]["type"] == "confirm"


def test_dialog_respond_sends_handler():
    buf, sock = cdp_buf()
    sock.frames = [{"id": 1, "result": {}}]
    push(buf, "Page.javascriptDialogOpening",
         {"type": "confirm", "message": "sure?"})
    buf.respond(accept=False)
    sent = [f for f in sock.sent
            if f.get("method") == "Page.handleJavaScriptDialog"]
    assert sent[-1]["params"]["accept"] is False
    assert buf.drain("dialogs") == []


def test_nav_events():
    buf, _ = cdp_buf()
    push(buf, "Page.frameNavigated",
         {"frame": {"url": "https://a/", "id": "f1"}})
    d = buf.drain("nav")
    assert d[0]["url"] == "https://a/"


def test_drain_all_returns_every_bucket():
    buf, _ = cdp_buf()
    push(buf, "Runtime.consoleAPICalled",
         {"type": "log", "args": [], "timestamp": 1})
    d = buf.drain()
    assert set(d) >= {"console", "errors", "requests", "dialogs", "nav"}


def test_bidi_events_classified():
    buf = ev.EventBuffer(None, "bidi")
    buf.ws = ScriptedSock()  # only needed for dialog responses
    import collections, threading
    buf.ws.events = collections.deque()
    buf.ws.sent = []
    buf.add({"method": "log.entryAdded",
             "params": {"type": "console", "level": "warn",
                        "text": "w", "timestamp": 1}})
    buf.add({"method": "network.beforeRequestSent",
             "params": {"request": {"request": "r1", "url": "https://b",
                                    "method": "POST"},
                        "context": "c1", "timestamp": 1}})
    buf.add({"method": "network.responseCompleted",
             "params": {"request": "r1",
                        "response": {"status": 201}, "timestamp": 2}})
    assert buf.drain("console")[0]["level"] == "warn"
    reqs = buf.drain("requests")
    assert reqs[0]["method"] == "POST" and reqs[0]["status"] == 201


def test_bidi_user_prompt():
    buf, sock = cdp_buf()
    buf.dialect = "bidi"
    buf.add({"method": "browsingContext.userPromptOpened",
             "params": {"context": "c1", "type": "confirm",
                        "message": "ok?"}})
    assert buf.drain("dialogs")[0]["type"] == "confirm"
    sock.frames = [{"id": 1, "result": {}}]
    buf.add({"method": "browsingContext.userPromptOpened",
             "params": {"context": "c1", "type": "alert", "message": "a"}})
    sent = [f for f in sock.sent
            if f.get("method") == "browsingContext.handleUserPrompt"]
    assert sent and sent[0]["params"]["accept"] is True


def test_events_deque_bounded():
    buf, _ = cdp_buf()
    assert buf.ws.events.maxlen == 2000


# -- daemon op dispatch -----------------------------------------------------------

def test_op_status_counts():
    buf, _ = cdp_buf()
    push(buf, "Runtime.consoleAPICalled",
         {"type": "log", "args": [], "timestamp": 1})
    r = ev._op(buf, "status", None)
    assert r["ok"] and r["dialect"] == "cdp"
    assert r["counts"]["console"] == 1


def test_op_har_writes_file(tmp_path):
    buf, _ = cdp_buf()
    push(buf, "Network.requestWillBeSent",
         {"requestId": "r1", "request": {"url": "u", "method": "GET"},
          "timestamp": 1.0})
    out = tmp_path / "h.json"
    r = ev._op(buf, "har", str(out))
    assert r["ok"] and r["entries"] == 1
    data = json.loads(out.read_text())
    assert data["entries"][0]["url"] == "u"


def test_op_stop_and_unknown():
    buf, _ = cdp_buf()
    assert ev._op(buf, "stop", None)["stopped"] is True
    assert ev._op(buf, "nope", None)["ok"] is False


def test_op_pin_delegates(monkeypatch, tmp_path):
    buf, _ = cdp_buf()
    monkeypatch.setattr(br, "_BINDING_OVERRIDE", str(tmp_path / "b.json"))
    br.bind("http://127.0.0.1:9222", 1)
    r = ev._op(buf, "pin", "t9")
    assert r["ok"] and br.binding()["target_id"] == "t9"
