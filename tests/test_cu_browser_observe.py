"""Gate: agent-browser port tier 1 — JS collector (console/errors/net),
wait, cookies/storage, find, tabs/pin, content boundaries. All via FakeWS —
no real browser."""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

hints = cu_load.load("cu_hints")
br = cu_load.load("cu_browser")


class FakeWS:
    """Scripted response ws: evaluate pops from a queue, commands recorded."""
    def __init__(self, eval_results=None):
        self.calls = []
        self.eval_results = list(eval_results or [])
        self.last_expr = ""

    def call(self, method, params=None):
        self.calls.append((method, params or {}))
        if method in ("Runtime.evaluate", "script.evaluate"):
            expr = (params or {}).get("expression", "")
            self.last_expr = expr
            val = self.eval_results.pop(0) if self.eval_results else None
            if method == "script.evaluate":
                return {"result": {"type": "number", "value": val}}
            return {"result": {"value": val}}
        return {}

    def close(self):
        pass


def cdp_client(eval_results=None):
    return br.BrowserClient(FakeWS(eval_results), "cdp", "t1")


def bidi_client(eval_results=None):
    return br.BrowserClient(FakeWS(eval_results), "bidi", "ctx1")


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "_BINDING_OVERRIDE", str(tmp_path / "b.json"))
    monkeypatch.setattr(hints, "session_id", lambda: "sess-test")
    yield


# -- collector --------------------------------------------------------------

def test_install_collector_cdp_uses_preload():
    c = cdp_client()
    r = c.install_collector()
    assert r["ok"] is True
    methods = [m for m, _ in c._ws.calls]
    assert "Page.addScriptToEvaluateOnNewDocument" in methods
    src = next(p["source"] for m, p in c._ws.calls
               if m == "Page.addScriptToEvaluateOnNewDocument")
    assert "__cu_log" in src and "__cu_net" in src and "__cu_errors" in src
    # live install on the already-loaded page too
    assert any(m == "Runtime.evaluate" for m, _ in c._ws.calls)


def test_install_collector_bidi_uses_preload():
    c = bidi_client()
    r = c.install_collector()
    assert r["ok"] is True
    methods = [m for m, _ in c._ws.calls]
    assert "script.addPreloadScript" in methods


def test_collector_returns_buffer():
    c = cdp_client(eval_results=[[{"level": "warn", "text": "x"}]])
    assert c.collector("log") == [{"level": "warn", "text": "x"}]
    assert "__cu_log" in c._ws.last_expr


def test_collector_clear_drains():
    c = cdp_client(eval_results=[[1, 2]])
    out = c.collector("net", clear=True)
    assert out == [1, 2]
    assert "splice" in c._ws.last_expr or "__cu_drain" in c._ws.last_expr


def test_collector_missing_returns_empty():
    c = cdp_client(eval_results=[None])
    assert c.collector("log") == []


# -- wait --------------------------------------------------------------------

def test_wait_fn_polls_until_truthy():
    c = cdp_client(eval_results=[False, False, True])
    r = c.wait(fn="window.ready === true", timeout=5.0, interval=0.01)
    assert r["ok"] is True
    assert len([m for m, _ in c._ws.calls if m == "Runtime.evaluate"]) == 3


def test_wait_fn_times_out():
    c = cdp_client(eval_results=[False] * 100)
    r = c.wait(fn="false", timeout=0.05, interval=0.01)
    assert r["ok"] is False
    assert r["reason"] == "timeout"


def test_wait_text_builds_inner_text_probe():
    c = cdp_client(eval_results=[True])
    r = c.wait(text="Welcome", timeout=1.0, interval=0.01)
    assert r["ok"] is True
    assert "innerText" in c._ws.last_expr and "Welcome" in c._ws.last_expr


def test_wait_selector_builds_query_probe():
    c = cdp_client(eval_results=[True])
    r = c.wait(selector="#main", timeout=1.0, interval=0.01)
    assert r["ok"] is True
    assert "querySelector" in c._ws.last_expr and "#main" in c._ws.last_expr


def test_wait_url_glob():
    c = cdp_client(eval_results=[True])
    r = c.wait(url="**/dash", timeout=1.0, interval=0.01)
    assert r["ok"] is True
    assert "location.href" in c._ws.last_expr


def test_wait_hidden_state():
    c = cdp_client(eval_results=[False])
    r = c.wait(selector="#spinner", state="hidden", timeout=1.0, interval=0.01)
    assert r["ok"] is True


# -- cookies / storage --------------------------------------------------------

def test_cookies_cdp():
    c = cdp_client()
    c._ws.call("Network.enable")
    c._ws.calls.clear()
    # fake the Network.getCookies result via a patched call
    c._ws.call = lambda m, p=None: (
        {"cookies": [{"name": "sid", "value": "v"}]} if m == "Network.getCookies"
        else {})
    out = c.cookies()
    assert out[0]["name"] == "sid"


def test_cookies_bidi():
    c = bidi_client()
    c._ws.call = lambda m, p=None: (
        {"cookies": [{"name": "sid", "value": {"type": "string",
                                              "value": "v"}}]}
        if m == "storage.getCookies" else {})
    out = c.cookies()
    assert isinstance(out, list)


def test_storage_ops():
    c = cdp_client(eval_results=["v1", None, True])
    assert c.storage("local", "get", "k") == "v1"
    assert "localStorage.getItem" in c._ws.last_expr
    c.storage("local", "set", "k", "v2")
    assert "localStorage.setItem" in c._ws.last_expr
    c.storage("local", "clear")
    assert "localStorage.clear" in c._ws.last_expr


def test_storage_session_area():
    c = cdp_client(eval_results=[None])
    c.storage("session", "get", "k")
    assert "sessionStorage" in c._ws.last_expr


# -- find --------------------------------------------------------------------

def test_find_role_queries_dom():
    els = [{"tag": "BUTTON", "role": "button", "name": "Submit",
            "bounds": [1, 2, 3, 4]}]
    c = cdp_client(eval_results=[els])
    out = c.find("role", "button", name="Submit")
    assert out[0]["name"] == "Submit"
    assert "role" in c._ws.last_expr


def test_find_text():
    c = cdp_client(eval_results=[[{"tag": "A", "text": "Sign In"}]])
    out = c.find("text", "Sign In")
    assert out[0]["text"] == "Sign In"


def test_find_returns_empty_on_no_match():
    c = cdp_client(eval_results=[[]])
    assert c.find("role", "button") == []


# -- tabs / pin ---------------------------------------------------------------

def test_tabs_cdp_lists_pages(monkeypatch):
    monkeypatch.setattr(br, "_http_json", lambda url, t=5.0: [
        {"type": "page", "id": "p1", "title": "A", "url": "https://a"},
        {"type": "worker", "id": "w1"},
        {"type": "page", "id": "p2", "title": "B", "url": "https://b"}])
    c = cdp_client()
    c.endpoint = "http://127.0.0.1:9222"
    tabs = c.tabs()
    assert [t["id"] for t in tabs] == ["p1", "p2"]


def test_tabs_bidi_lists_top_contexts():
    c = bidi_client()
    c._ws.call = lambda m, p=None: (
        {"contexts": [{"context": "c1", "url": "u1"},
                      {"context": "c2", "url": "u2", "parent": "c1"}]}
        if m == "browsingContext.getTree" else {})
    tabs = c.tabs()
    assert [t["id"] for t in tabs] == ["c1"]


def test_pin_writes_target_into_binding():
    br.bind("http://127.0.0.1:9222", 4321)
    r = br.pin_target("p2")
    assert r["ok"] is True
    assert br.binding()["target_id"] == "p2"


def test_discover_cdp_honors_pin(monkeypatch):
    monkeypatch.setattr(br, "_http_json", lambda url, t=5.0: [
        {"type": "page", "id": "p1", "webSocketDebuggerUrl": "ws://x/1"},
        {"type": "page", "id": "p2", "webSocketDebuggerUrl": "ws://x/2"}])
    found = br._discover_cdp("http://127.0.0.1:9222", 5.0, target_id="p2")
    assert found == ("ws://x/2", "p2")


def test_unpin_removes_target():
    br.bind("http://127.0.0.1:9222", 4321)
    br.pin_target("p2")
    br.pin_target(None)
    assert "target_id" not in br.binding()


# -- boundaries ----------------------------------------------------------------

def test_boundaries_wrap_marks_untrusted():
    out = br.boundaries("page text")
    assert "UNTRUSTED" in out.split("\n")[0]
    assert "page text" in out
    assert out.rstrip().endswith("---")
