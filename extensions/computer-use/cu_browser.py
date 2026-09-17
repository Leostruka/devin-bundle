#!/usr/bin/env python3
"""Authorized-browser binding contract.

DOM/ARIA/CDP targeting is only ever allowed against a browser the caller
explicitly bound for THIS automation session. Nothing here launches a
browser, enables remote debugging, or attaches to a foreign session.

Binding lives in <temp>/devin-cu-browser.json with the same session+TTL
rules as the hint sidecar: a new session_id or an expired binding rejects.

    bind(endpoint, pid)   -> writes the binding file (explicit, opt-in)
    unbind()              -> removes it
    binding()             -> dict | None
    check(hwnd)           -> (allowed: bool, reason: str|None)
    viewport_to_desktop() -> CSS px -> desktop px (never implicit)

The CDP client itself stays a seam: `_cdp_client()` returns None unless an
approved driver module is importable — honest "unavailable", never silent.
"""
import json
import os
import tempfile
import time

import cu_hints

BINDING_TTL_S = float(os.environ.get("CU_BROWSER_TTL", "600"))
_BINDING_OVERRIDE = None  # tests inject a path here


def _path():
    if _BINDING_OVERRIDE:
        return _BINDING_OVERRIDE
    return os.path.join(tempfile.gettempdir(), "devin-cu-browser.json")


def bind(endpoint, pid):
    """Record an explicitly-authorized browser for this session.

    endpoint: e.g. "http://127.0.0.1:9222" — loopback only.
    pid:      OS process id of the browser to constrain targeting to.
    """
    if not isinstance(endpoint, str) or not endpoint.startswith(
            ("http://127.0.0.1", "http://localhost", "https://127.0.0.1",
             "https://localhost")):
        return {"ok": False, "error": "endpoint must be loopback (127.0.0.1/localhost)"}
    if not isinstance(pid, int) or pid <= 0:
        return {"ok": False, "error": "pid must be a positive int"}
    data = {"endpoint": endpoint, "pid": pid,
            "session_id": cu_hints.session_id(),
            "created_at": time.time()}
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, _path())
    return {"ok": True, "binding": data}


def unbind():
    try:
        os.remove(_path())
    except OSError:
        pass
    return {"ok": True}


def binding():
    """Current binding dict if valid for this session, else None."""
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if data.get("session_id") != cu_hints.session_id():
        return None
    if time.time() - data.get("created_at", 0) > BINDING_TTL_S:
        return None
    return data


def _hwnd_pid(hwnd):
    """pid owning hwnd; 0 if unavailable. Separated for test injection."""
    if os.name != "nt":
        return 0
    import ctypes
    pid = ctypes.c_ulong(0)
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def check(hwnd):
    """May we semantically target the element at hwnd?
    Returns (allowed, reason). reason None on success, else typed code —
    callers must NOT use DOM/CDP when reason is set."""
    b = binding()
    if b is None:
        return False, "no_binding"
    pid = _hwnd_pid(hwnd)
    if not pid:
        return False, "unknown_owner"
    if pid != b["pid"]:
        return False, "foreign_process"
    return True, None


class _WSClient:
    """Thin JSON-RPC over one websocket. dialect: "cdp" (Chromium) or
    "bidi" (Firefox/Zen — WebDriver BiDi). suppress_origin avoids the
    remote-allow-origins handshake check on both engines."""

    def __init__(self, url, dialect, timeout=10.0):
        import websocket
        self.dialect = dialect
        self.ws = websocket.create_connection(
            url, timeout=timeout, suppress_origin=True)
        self._id = 0
        self.context = None  # bidi browsingContext / cdp target page

    def call(self, method, params=None):
        self._id += 1
        self.ws.send(json.dumps(
            {"id": self._id, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") != self._id:
                continue  # event frame — skip
            if self.dialect == "bidi":
                if msg.get("type") == "error":
                    raise RuntimeError(
                        f"{msg.get('error')}: {msg.get('message')}")
                return msg.get("result")
            if "error" in msg:
                raise RuntimeError(str(msg["error"]))
            return msg.get("result")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def _http_json(url, timeout=5.0):
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _bidi_value(v):
    """Unwrap a BiDi remote value to a plain Python value (recursive for
    arrays/objects)."""
    if not isinstance(v, dict):
        return v
    t = v.get("type")
    if t == "undefined":
        return None
    val = v.get("value")
    if t == "array" and isinstance(val, list):
        return [_bidi_value(x) for x in val]
    if t == "object" and isinstance(val, list):
        return {k: _bidi_value(x) for k, x in val}
    return val if "value" in v else v


class BrowserClient:
    """Bound-browser semantic client: evaluate / click / screenshot over
    CDP or BiDi. Coordinates are CSS px in viewport space — callers convert
    with viewport_to_desktop for physical input paths."""

    def __init__(self, ws, dialect, target):
        self._ws = ws
        self.dialect = dialect
        self.target = target  # page target id (cdp) | browsingContext (bidi)

    def evaluate(self, expression):
        if self.dialect == "cdp":
            r = self._ws.call("Runtime.evaluate", {
                "expression": expression, "returnByValue": True})
            return (r.get("result") or {}).get("value")
        r = self._ws.call("script.evaluate", {
            "expression": expression,
            "target": {"context": self.target},
            "awaitPromise": False})
        return _bidi_value((r or {}).get("result"))

    def click(self, x, y):
        """Semantic click at CSS-px viewport coords."""
        if self.dialect == "cdp":
            for t in ("mousePressed", "mouseReleased"):
                self._ws.call("Input.dispatchMouseEvent", {
                    "type": t, "x": x, "y": y,
                    "button": "left", "clickCount": 1})
            return
        self._ws.call("input.performActions", {
            "context": self.target,
            "actions": [{"type": "pointer", "id": "m",
                         "parameters": {"pointerType": "mouse"},
                         "actions": [
                             {"type": "pointerMove", "x": int(x),
                              "y": int(y), "origin": "viewport"},
                             {"type": "pointerDown", "button": 0},
                             {"type": "pointerUp", "button": 0}]}]})

    def navigate(self, url):
        if self.dialect == "cdp":
            return self._ws.call("Page.navigate", {"url": url})
        return self._ws.call("browsingContext.navigate",
                             {"context": self.target, "url": url,
                              "wait": "complete"})

    def screenshot(self):
        """Viewport PNG, base64."""
        if self.dialect == "cdp":
            return self._ws.call("Page.captureScreenshot",
                                 {"format": "png"}).get("data")
        return self._ws.call("browsingContext.captureScreenshot",
                             {"context": self.target}).get("data")

    def close(self):
        self._ws.close()


def _discover_cdp(endpoint, timeout):
    """Chromium: /json/list -> first page target ws url."""
    try:
        pages = _http_json(endpoint.rstrip("/") + "/json/list", timeout)
    except Exception:
        return None
    for t in pages:
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            return t["webSocketDebuggerUrl"], t.get("id")
    return None


def _connect_bidi(endpoint, timeout):
    """Gecko: ws endpoint at /session; session.new then getTree. Fresh
    profiles can expose stale 0x0 top-level contexts — probe innerWidth and
    pick the first painted one; fallback to the last context."""
    host = endpoint.rstrip("/").split("://", 1)[-1]
    ws = _WSClient(f"ws://{host}/session", "bidi", timeout)
    ws.call("session.new", {"capabilities": {}})
    tree = ws.call("browsingContext.getTree", {})
    ctxs = [c["context"] for c in (tree or {}).get("contexts", [])
            if not c.get("parent")]
    if not ctxs:
        ws.close()
        raise RuntimeError("bidi: no browsing context")
    pick = ctxs[-1]
    for ctx in ctxs:
        try:
            r = ws.call("script.evaluate", {
                "expression": "innerWidth",
                "target": {"context": ctx}, "awaitPromise": False})
            if _bidi_value((r or {}).get("result")):
                pick = ctx
                break
        except Exception:
            continue
    return ws, pick


def _cdp_client(timeout=10.0):
    """Attach to the bound browser. Returns BrowserClient or None when
    unbound / driver missing / endpoint unreachable. Never raises."""
    b = binding()
    if b is None:
        return None
    try:
        import websocket  # noqa: F401
    except ImportError:
        return None
    ep = b["endpoint"]
    try:
        found = _discover_cdp(ep, timeout)
        if found:
            ws_url, tid = found
            ws = _WSClient(ws_url, "cdp", timeout)
            for dom in ("Page.enable", "Runtime.enable"):
                try:
                    ws.call(dom)
                except Exception:
                    pass
            return BrowserClient(ws, "cdp", tid)
        ws, ctx = _connect_bidi(ep, timeout)
        return BrowserClient(ws, "bidi", ctx)
    except Exception:
        return None


def viewport_to_desktop(css_x, css_y, viewport_origin, dpr=1.0):
    """CSS px -> desktop physical px. Callers MUST supply the viewport's
    top-left corner in desktop px and the device pixel ratio; mixing the two
    spaces without conversion is the bug this signature exists to prevent."""
    ox, oy = viewport_origin
    return round(css_x * dpr + ox), round(css_y * dpr + oy)
