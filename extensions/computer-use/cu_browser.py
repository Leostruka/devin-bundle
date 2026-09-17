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


def _cdp_client():
    """Approved driver seam. Returns a client or None — None means DOM/CDP
    targeting is unavailable and callers must use the visual path."""
    return None


def viewport_to_desktop(css_x, css_y, viewport_origin, dpr=1.0):
    """CSS px -> desktop physical px. Callers MUST supply the viewport's
    top-left corner in desktop px and the device pixel ratio; mixing the two
    spaces without conversion is the bug this signature exists to prevent."""
    ox, oy = viewport_origin
    return round(css_x * dpr + ox), round(css_y * dpr + oy)
