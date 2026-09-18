"""Gate for ticket 09: --via browser routing. Bound hwnd -> DOM dispatch;
unbound/foreign -> typed reject with zero physical/browser calls."""
import json
import os
import subprocess
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

hints = cu_load.load("cu_hints")
br = cu_load.load("cu_browser")


class FakeWS:
    hit = {"ok": True, "tag": "BUTTON"}

    def __init__(self):
        self.calls = []
        self.hit = {"ok": True, "tag": "BUTTON"}

    def call(self, method, params=None):
        self.calls.append(method)
        if method == "Runtime.evaluate":
            expr = (params or {}).get("expression", "")
            if "FromPoint" in expr:
                return {"result": {"value": self.hit}}
            return {"result": {"value": 1.0}}  # devicePixelRatio
        return {}

    def close(self):
        pass


class FakeClient(br.BrowserClient):
    def __init__(self):
        super().__init__(FakeWS(), "cdp", "t1")


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "_BINDING_OVERRIDE", str(tmp_path / "b.json"))
    monkeypatch.setattr(hints, "sidecar_path",
                        lambda: str(tmp_path / "h.json"))
    monkeypatch.setattr(hints, "session_path",
                        lambda: str(tmp_path / "s.json"))
    monkeypatch.setattr(hints, "_window_alive", lambda hwnd: True)
    monkeypatch.setattr(br, "_hwnd_pid", lambda hwnd: 4321)
    monkeypatch.setattr(br, "_client_origin", lambda hwnd: (100, 50))
    yield


def _hint(hwnd=4321):
    return hints.write_sidecar(
        [{"id": "a", "x": 500, "y": 300, "name": "Btn", "type": "Button",
          "bounds": [490, 290, 530, 320], "hwnd": hwnd, "enabled": True}],
        window={"hwnd": hwnd})


def test_dom_click_bound_window(monkeypatch):
    _hint()
    br.bind("http://127.0.0.1:9222", 4321)
    cli = FakeClient()
    monkeypatch.setattr(br, "_cdp_client", lambda timeout=10.0: cli)
    res, reason = br.dom_action(4321, 500, 300, "click")
    assert reason is None and res["backend"] == "dom"
    # desktop (500,300) - client origin (100,50), dpr 1.0 -> css 400,250
    assert res["css"] == [400.0, 250.0]
    assert "Input.dispatchMouseEvent" in cli._ws.calls


def test_dom_action_unbound_rejects():
    _hint()
    res, reason = br.dom_action(4321, 500, 300, "click")
    assert res is None and reason == "browser_no_binding"


def test_dom_action_foreign_pid_rejects():
    _hint()
    br.bind("http://127.0.0.1:9222", 9999)  # bound to a DIFFERENT pid
    res, reason = br.dom_action(4321, 500, 300, "click")
    assert res is None and reason == "browser_foreign_process"


def test_dom_action_no_client_rejects(monkeypatch):
    _hint()
    br.bind("http://127.0.0.1:9222", 4321)
    monkeypatch.setattr(br, "_cdp_client", lambda timeout=10.0: None)
    res, reason = br.dom_action(4321, 500, 300, "click")
    assert res is None and reason == "browser_unavailable"


def test_dom_type_focus_then_insert(monkeypatch):
    _hint()
    br.bind("http://127.0.0.1:9222", 4321)
    cli = FakeClient()
    monkeypatch.setattr(br, "_cdp_client", lambda timeout=10.0: cli)
    res, reason = br.dom_action(4321, 500, 300, "type", text="oi")
    assert reason is None and res["typed"] == 2
    assert "Input.dispatchMouseEvent" in cli._ws.calls  # focus click
    assert "Input.insertText" in cli._ws.calls


def test_mouse_via_browser_no_hint_fails():
    """--via browser without --hint must reject — no hwnd to authorize."""
    env = dict(os.environ, PYTHONPATH=str(cu_load.EXT))
    r = subprocess.run(
        [sys.executable, str(cu_load.EXT / "mouse.py"),
         "click", "10", "10", "--via", "browser"],
        capture_output=True, text=True, env=env)
    out = json.loads(r.stdout)
    assert out["ok"] is False and "requires --hint" in out["error"]


def test_mouse_via_browser_stale_hint_zero_dispatch():
    """Stale hint + --via browser: rejection happens before ANY backend."""
    env = dict(os.environ, PYTHONPATH=str(cu_load.EXT))
    r = subprocess.run(
        [sys.executable, str(cu_load.EXT / "mouse.py"),
         "click", "--hint", "zz", "--via", "browser"],
        capture_output=True, text=True, env=env)
    out = json.loads(r.stdout)
    assert out["ok"] is False and "rejected" in out["error"]


# --- Ticket 10: actionability gate -------------------------------------------

def _bound_fake(monkeypatch, hit):
    _hint()
    br.bind("http://127.0.0.1:9222", 4321)
    cli = FakeClient()
    cli._ws.hit = hit  # per-instance — no cross-test class mutation
    monkeypatch.setattr(br, "_cdp_client", lambda timeout=10.0: cli)
    return cli


def test_actionable_covered_rejects(monkeypatch):
    _bound_fake(monkeypatch, {"ok": False, "reason": "covered"})
    res, reason = br.dom_action(4321, 500, 300, "click", wait=0.05)
    assert res is None and reason == "browser_actionable_covered"


def test_actionable_disabled_hint_rejects():
    _hint()
    br.bind("http://127.0.0.1:9222", 4321)
    res, reason = br.dom_action(4321, 500, 300, "click", enabled=False)
    assert res is None and reason == "browser_disabled"


def test_actionable_zero_size_rejects_fast(monkeypatch):
    _bound_fake(monkeypatch, {"ok": False, "reason": "zero_size"})
    res, reason = br.dom_action(4321, 500, 300, "click", wait=5.0)
    assert res is None and reason == "browser_actionable_zero_size"


# --- Ticket 11: context scoping -----------------------------------------------

def test_evaluate_in_foreign_context_cdp_rejects(monkeypatch):
    _bound_fake(monkeypatch, {"ok": True, "tag": "BUTTON"})
    cli = br._cdp_client.__wrapped__ if hasattr(
        br._cdp_client, "__wrapped__") else FakeClient()
    monkeypatch.setattr(br, "_cdp_client", lambda timeout=10.0: cli)
    with pytest.raises(RuntimeError, match="cdp_context"):
        cli.evaluate_in("1", context="other-frame")


def test_bidi_contexts_listed():
    ws = FakeWS()
    cli = br.BrowserClient(ws, "bidi", "ctx-main")
    ws.call = lambda m, p=None: (
        {"contexts": [{"context": "ctx-main"},
                      {"context": "ctx-iframe", "parent": "ctx-main"}]}
        if m == "browsingContext.getTree" else {})
    assert cli.contexts() == ["ctx-main", "ctx-iframe"]


# --- Ticket 12: canvas -> declared visual fallback ----------------------------

def test_canvas_hit_rejects_dom(monkeypatch):
    _bound_fake(monkeypatch, {"ok": False, "reason": "canvas",
                              "tag": "CANVAS"})
    res, reason = br.dom_action(4321, 500, 300, "click", wait=0.05)
    assert res is None and reason == "browser_actionable_canvas"


def test_bounds_px_reaches_actionable_gate(monkeypatch):
    """bounds_css must actually be wired — covered verdict only exists when
    the element's expected bounds are passed through."""
    cli = _bound_fake(monkeypatch, {"ok": False, "reason": "covered"})
    seen = {}

    def spy(cx, cy, bounds_css=None, timeout=3.0, interval=0.15):
        seen["bounds"] = bounds_css
        return {"ok": False, "reason": "covered"}

    monkeypatch.setattr(cli, "wait_actionable", spy)
    res, reason = br.dom_action(4321, 500, 300, "click", wait=0.01,
                                bounds_px=[490, 290, 40, 30])
    assert reason == "browser_actionable_covered"
    assert seen["bounds"] == [390.0, 240.0, 40.0, 30.0]  # origin (100,50), dpr 1
