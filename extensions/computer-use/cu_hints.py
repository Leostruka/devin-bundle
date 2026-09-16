#!/usr/bin/env python3
"""Vimium-style hint extraction via Windows UI Automation.

enum_clickables() returns on-screen interactive elements of the focused
window (or all windows) with physical-pixel rects, or None on any failure —
callers fall back to the pixel grid. Runs in a daemon thread so a stuck
UIA provider can never hang the caller.

Sidecar: <temp>/devin-cu-hints.json — {hint-id: {x, y, name, type}} so
`mouse.py click --hint <id>` can resolve exact centers.
"""
import io
import json
import os
import queue
import tempfile
import threading
from contextlib import redirect_stdout

HINT_CHARS = "sadfjklewcmpgh"  # vimium-style home-row alphabet
MAX_HINTS = len(HINT_CHARS) ** 2  # 196

# UIA ControlType id -> short label
CLICKABLE = {50000: "Button", 50002: "CheckBox", 50003: "ComboBox",
             50004: "Edit", 50005: "Link", 50006: "Image",
             50007: "ListItem", 50011: "MenuItem", 50013: "RadioButton",
             50019: "TabItem", 50024: "TreeItem", 50029: "DataItem",
             50031: "SplitButton", 50035: "HeaderItem"}

_PID_CONTROL_TYPE = 30003
_PID_IS_OFFSCREEN = 30022
_PID_HWND = 30020
_SCOPE_CHILDREN = 0x2
_SCOPE_DESCENDANTS = 0x4


def _enum_worker(scope):
    import comtypes
    try:
        comtypes.CoInitialize()
    except Exception:
        pass
    try:
        with redirect_stdout(io.StringIO()):
            import uiautomation as auto
            from uiautomation.uiautomation import _AutomationClient
        core = _AutomationClient.instance().IUIAutomation
        orcond = None
        for ct in CLICKABLE:
            c = core.CreatePropertyCondition(_PID_CONTROL_TYPE, ct)
            orcond = c if orcond is None else core.CreateOrCondition(orcond, c)
        cond = core.CreateAndCondition(
            orcond, core.CreatePropertyCondition(_PID_IS_OFFSCREEN, False))
        root = auto.GetRootControl().Element
        target = root
        if scope == "focused":
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd:
                el = root.FindFirst(
                    _SCOPE_CHILDREN,
                    core.CreatePropertyCondition(_PID_HWND, hwnd))
                if el:
                    target = el
        arr = target.FindAll(_SCOPE_DESCENDANTS, cond)
        out = []
        for i in range(arr.Length):
            e = arr.GetElement(i)
            r = e.CurrentBoundingRectangle
            w, h = r.right - r.left, r.bottom - r.top
            if w < 4 or h < 4:
                continue
            try:
                nm = (e.CurrentName or "")[:80]
            except Exception:
                nm = ""
            out.append({"type": CLICKABLE.get(e.CurrentControlType, "?"),
                        "x": (r.left + r.right) // 2,
                        "y": (r.top + r.bottom) // 2,
                        "rx": r.left, "ry": r.top, "w": w, "h": h,
                        "name": nm})
        return out
    finally:
        try:
            comtypes.CoUninitialize()
        except Exception:
            pass


def enum_clickables(scope="focused", timeout=6.0):
    """Return sorted unique element list, or None on failure/timeout."""
    if os.environ.get("CU_NO_UIA"):
        return None
    if os.name != "nt":
        return None
    q = queue.Queue(maxsize=1)
    t = threading.Thread(target=lambda: _put(q, scope), daemon=True)
    t.start()
    try:
        els = q.get(timeout=timeout)
    except queue.Empty:
        return None
    if not els:
        return None
    seen, uniq = set(), []
    for e in els:
        k = (e["type"], e["x"], e["y"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    uniq.sort(key=lambda e: (e["ry"], e["rx"]))
    return uniq[:MAX_HINTS]


def _put(q, scope):
    try:
        q.put(_enum_worker(scope))
    except Exception:
        q.put(None)


def hint_ids(n):
    """n unique labels: single chars while they fit, else two-char."""
    a = HINT_CHARS
    if n <= len(a):
        return list(a[:n])
    return [x + y for x in a for y in a][:n]


def sidecar_path():
    return os.path.join(tempfile.gettempdir(), "devin-cu-hints.json")


def write_sidecar(hints):
    data = {"hints": {h["id"]: {"x": h["x"], "y": h["y"],
                                "name": h["name"], "type": h["type"]}
                      for h in hints}}
    with open(sidecar_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def resolve_hint(hint_id):
    """Return (x, y, name) for a hint id from the sidecar, else None."""
    try:
        with open(sidecar_path(), encoding="utf-8") as f:
            e = json.load(f).get("hints", {}).get(hint_id.lower())
    except Exception:
        return None
    if not e:
        return None
    return e["x"], e["y"], e.get("name", "")
