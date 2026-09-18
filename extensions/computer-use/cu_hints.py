#!/usr/bin/env python3
"""Vimium-style hint extraction via Windows UI Automation.

enum_clickables() returns {"elements", "window", "truncated"} for the
focused window (or all windows) with physical-pixel bounds, or None on any
failure — callers fall back to the pixel grid. Runs in a daemon thread so a
stuck UIA provider can never hang the caller.

Sidecar: <temp>/devin-cu-hints.json — schema_version 2 with session_id,
generation, window binding and per-hint {x, y, name, type, bounds, hwnd,
enabled}. `mouse.py click --hint <id>` resolves exact centers through
resolve_hint(), which rejects stale/expired/foreign-session hints with a
typed reason instead of returning coordinates blindly.

uia_perform(entry, action, ...) re-locates a sidecar element live (by hwnd +
type + nearest bounds) and runs a UIA pattern — Invoke or Value.SetValue —
for semantic actions. Failure reasons are typed: "stale", "no_pattern",
"readonly", "no_hwnd", "timeout", "error:<exc>".
"""
import io
import json
import os
import queue
import tempfile
import threading
import time
import uuid
from contextlib import redirect_stdout

HINT_CHARS = "sadfjklewcmpgh"  # vimium-style home-row alphabet
MAX_HINTS = len(HINT_CHARS) ** 2  # 196
HINT_TTL_S = float(os.environ.get("CU_HINT_TTL", "120"))
SCHEMA_VERSION = 2
_SIDECAR_LOCK = threading.Lock()

# UIA ControlType id -> short label
CLICKABLE = {50000: "Button", 50002: "CheckBox", 50003: "ComboBox",
             50004: "Edit", 50005: "Link", 50006: "Image",
             50007: "ListItem", 50011: "MenuItem", 50013: "RadioButton",
             50019: "TabItem", 50024: "TreeItem", 50029: "DataItem",
             50031: "SplitButton", 50035: "HeaderItem"}

_PID_CONTROL_TYPE = 30003
_PID_IS_OFFSCREEN = 30022
_PID_HWND = 30020
_PID_BOUNDS = 30001
_PID_NAME = 30005
_PID_ENABLED = 30010
_SCOPE_CHILDREN = 0x2
_SCOPE_DESCENDANTS = 0x4

_PAT_INVOKE = 10000
_PAT_VALUE = 10002


def _com_thread(fn):
    """Run fn() on a COM-initialized daemon thread; return its result or
    None on exception (timeout is the caller's concern via the queue).

    Every COM object must be created, used and released on this thread —
    see _uia_core() and the _el strip in _enum_impl. CoUninitialize in
    finally is safe ONLY because all releases are frame-scoped and happen
    before it runs."""
    try:
        import comtypes
        try:
            comtypes.CoInitialize()
        except Exception:
            pass
        try:
            return fn()
        finally:
            try:
                comtypes.CoUninitialize()
            except Exception:
                pass
    except Exception:
        return None


def _uia_core():
    """Fresh IUIAutomation bound to the CALLING thread's apartment.

    NOT uiautomation's _AutomationClient singleton: that object ties its
    COM interfaces to whichever thread created it first — a second
    worker's calls then run against a dead apartment, and the singleton's
    release at process exit RPC_E_DISCONNECTEDs into an access violation
    (the --hints segfault). A per-call client keeps every COM object's
    lifetime inside one apartment."""
    with redirect_stdout(io.StringIO()):
        import comtypes.client
        mod = comtypes.client.GetModule("UIAutomationCore.dll")
    return comtypes.client.CreateObject(
        "{ff48dba4-60ef-4201-aa87-54103eef594e}",
        interface=mod.IUIAutomation)


def _clickable_cond(core):
    orcond = None
    for ct in CLICKABLE:
        c = core.CreatePropertyCondition(_PID_CONTROL_TYPE, ct)
        orcond = c if orcond is None else core.CreateOrCondition(orcond, c)
    return core.CreateAndCondition(
        orcond, core.CreatePropertyCondition(_PID_IS_OFFSCREEN, False))


def _enum_elements(core, target):
    """Clickable descendants of target. Uses FindAllBuildCache when the
    provider supports it (one round-trip instead of per-element Current
    reads); falls back to FindAll + live property reads."""
    cond = _clickable_cond(core)
    arr, cached = None, False
    if not os.environ.get("CU_HINT_NOCACHE"):
        try:
            req = core.CreateCacheRequest()
            for pid in (_PID_NAME, _PID_CONTROL_TYPE, _PID_BOUNDS,
                        _PID_ENABLED, _PID_IS_OFFSCREEN, _PID_HWND):
                req.AddProperty(pid)
            arr = target.FindAllBuildCache(_SCOPE_DESCENDANTS, cond, req)
            cached = True
        except Exception:
            pass
    if arr is None:
        arr = target.FindAll(_SCOPE_DESCENDANTS, cond)
    out = []
    for i in range(arr.Length):
        e = arr.GetElement(i)
        try:
            if cached:
                r, ct = e.CachedBoundingRectangle, e.CachedControlType
                nm, en = e.CachedName, e.CachedIsEnabled
                wh = e.CachedNativeWindowHandle
            else:
                r, ct = e.CurrentBoundingRectangle, e.CurrentControlType
                nm, en = e.CurrentName, e.CurrentIsEnabled
                wh = e.CurrentNativeWindowHandle
        except Exception:
            continue
        w, h = r.right - r.left, r.bottom - r.top
        if w < 4 or h < 4:
            continue
        out.append({"type": CLICKABLE.get(ct, "?"),
                    "x": (r.left + r.right) // 2,
                    "y": (r.top + r.bottom) // 2,
                    "bounds": [r.left, r.top, w, h],
                    "enabled": bool(en),
                    "hwnd": int(wh) if wh else None,
                    "name": (nm or "")[:80],
                    "_el": e})
    return out


def _foreground():
    """(hwnd, pid) of the current foreground window, or (0, 0)."""
    import ctypes
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    pid = 0
    if hwnd:
        p = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(
            hwnd, ctypes.byref(p))
        pid = p.value
    return hwnd, pid


def _enum_impl(scope, hwnd=None):
    core = _uia_core()
    if hwnd:
        target = core.ElementFromHandle(hwnd)
        els, win = _enum_elements(core, target), None
    else:
        root = core.GetRootElement()
        fg, pid = _foreground()
        win = {"hwnd": fg, "pid": pid, "foreground": True} if fg else None
        target = root
        if scope == "focused":
            if not fg:
                return [], None
            el = root.FindFirst(
                _SCOPE_CHILDREN, core.CreatePropertyCondition(_PID_HWND, fg))
            if not el:
                return [], win  # never broaden a focused query to the desktop
            target = el
        els = _enum_elements(core, target)
    # COM objects die HERE, on their own apartment — a queued _el released
    # later on the caller's thread RPC_E_DISCONNECTEDs into an AV.
    for e in els:
        e.pop("_el", None)
    return els, win


def _enum_worker(scope):
    return _com_thread(lambda: _enum_impl(scope))


def enum_clickables(scope="focused", timeout=6.0):
    """Return {"elements", "window", "truncated"} or None on
    failure/timeout/empty."""
    if os.environ.get("CU_NO_UIA") or os.name != "nt":
        return None
    q = queue.Queue(maxsize=1)
    t = threading.Thread(target=lambda: _put(q, scope), daemon=True)
    t.start()
    try:
        res = q.get(timeout=timeout)
    except queue.Empty:
        return None
    if not res:
        return None
    els, win = res
    if not els:
        return None
    seen, uniq = set(), []
    for e in els:
        k = (e["type"], e["x"], e["y"])
        if k in seen:
            continue
        seen.add(k)
        e.pop("_el", None)  # COM objects never leave the worker thread
        uniq.append(e)
    uniq.sort(key=lambda e: (e["bounds"][1], e["bounds"][0]))
    return {"elements": uniq[:MAX_HINTS], "window": win,
            "truncated": len(uniq) > MAX_HINTS}


def _put(q, scope):
    try:
        q.put(_enum_worker(scope))
    except Exception:
        q.put(None)


# --- live re-location + semantic actions -------------------------------------

def _nearest(els, entry):
    """Re-locate the recorded element among current candidates. Binding:
    same control type AND (when recorded) same name, within a distance
    tolerance proportional to the element's size — a same-type element at
    an unrelated position is NOT the same control."""
    b = entry.get("bounds") or [0, 0, 0, 0]  # [l, t, w, h]
    diag = (b[2] ** 2 + b[3] ** 2) ** 0.5
    tol2 = max(64.0, diag * 1.5) ** 2
    name = (entry.get("name") or "").strip()
    best, bd = None, None
    for e in els:
        if e["type"] != entry.get("type"):
            continue
        if name and (e.get("name") or "").strip() != name:
            continue
        d = (e["x"] - entry["x"]) ** 2 + (e["y"] - entry["y"]) ** 2
        if d > tol2:
            continue
        if bd is None or d < bd:
            best, bd = e, d
    return best


def _perform_impl(entry, action, text):
    core = _uia_core()
    if not entry.get("hwnd"):
        return None, "no_hwnd"
    target = core.ElementFromHandle(entry["hwnd"])
    els = _enum_elements(core, target)
    best = _nearest(els, entry)
    if best is None:
        return None, "stale"
    el, (l, t, w, h) = best["_el"], best["bounds"]
    cx, cy = l + w // 2, t + h // 2
    if action == "locate":
        return {"x": cx, "y": cy}, None
    if action == "invoke":
        pat = el.GetCurrentPattern(_PAT_INVOKE)
        if pat is None:
            return {"x": cx, "y": cy}, "no_pattern"
        pat.Invoke()
        return {"x": cx, "y": cy, "pattern": "Invoke"}, None
    if action == "set_value":
        pat = el.GetCurrentPattern(_PAT_VALUE)
        if pat is None:
            return {"x": cx, "y": cy}, "no_pattern"
        try:
            if pat.CurrentIsReadOnly:
                return {"x": cx, "y": cy}, "readonly"
        except Exception:
            pass
        pat.SetValue(text)
        return {"x": cx, "y": cy, "pattern": "Value"}, None
    return None, "bad_action"


def uia_perform(entry, action, text=None, timeout=4.0):
    """Re-locate a sidecar element live and run a UIA pattern on it.
    Returns (result_dict, reason). result_dict has the element's CURRENT
    center — re-resolution, not the recorded coordinates. NOTE: result may
    be non-None alongside a failure reason (coordinates for diagnostics) —
    callers must check `reason is None`, not truthiness."""
    if entry.get("enabled") is False:
        return None, "disabled"
    if os.environ.get("CU_NO_UIA") or os.name != "nt":
        return None, "no_uia"
    q = queue.Queue(maxsize=1)
    def run():
        try:
            q.put(_com_thread(lambda: _perform_impl(entry, action, text)))
        except Exception as e:
            q.put((None, f"error:{type(e).__name__}"))
    threading.Thread(target=run, daemon=True).start()
    try:
        res = q.get(timeout=timeout)
    except queue.Empty:
        return None, "timeout"
    if res is None:
        return None, "error"
    return res


# --- sidecar -----------------------------------------------------------------

def hint_ids(n):
    """n unique labels: single chars while they fit, else two-char."""
    a = HINT_CHARS
    if n <= len(a):
        return list(a[:n])
    return [x + y for x in a for y in a][:n]


def sidecar_path():
    return os.path.join(tempfile.gettempdir(), "devin-cu-hints.json")


def session_path():
    return os.path.join(tempfile.gettempdir(), "devin-cu-session.json")


def session_id():
    """Stable id for this local automation session (auto-created)."""
    try:
        with open(session_path(), encoding="utf-8") as f:
            sid = json.load(f).get("session_id")
        if sid:
            return sid
    except Exception:
        pass
    sid = uuid.uuid4().hex[:12]
    try:
        with open(session_path(), "w", encoding="utf-8") as f:
            json.dump({"session_id": sid}, f)
    except Exception:
        pass
    return sid


def _read_sidecar():
    try:
        with open(sidecar_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _next_generation():
    """Monotonic generation counter persisted in the session file —
    survives sidecar invalidation (the file is deleted, the session is
    not), so a stale --gen pin can never resolve a later observation."""
    try:
        with open(session_path(), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    gen = int(d.get("next_generation", 0)) + 1
    d["session_id"] = d.get("session_id") or session_id()
    d["next_generation"] = gen
    tmp = session_path() + f".{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, session_path())
    except Exception:
        pass
    return gen


def _fs_lock():
    """Cross-process byte lock on a sibling .lock file (msvcrt on Windows;
    thread-lock only elsewhere — real snapshots are separate processes)."""
    if os.name != "nt":
        return None
    import msvcrt
    f = open(sidecar_path() + ".lock", "a+b")
    f.seek(0)
    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
    return f


def _fs_unlock(f):
    if f is None:
        return
    import msvcrt
    f.seek(0)
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        f.close()


def write_sidecar(hints, window=None, capture=None):
    """Atomic sidecar write; returns the observation dict written.
    Serialized by _SIDECAR_LOCK (threads) + a file byte-lock (processes):
    concurrent writers get monotonic generations and never share tmp."""
    with _SIDECAR_LOCK:
        f = _fs_lock()
        try:
            return _write_sidecar_locked(hints, window, capture)
        finally:
            _fs_unlock(f)


def _write_sidecar_locked(hints, window, capture):
    generation = _next_generation()
    data = {"schema_version": SCHEMA_VERSION,
            "session_id": session_id(),
            "observation_id": f"obs-{generation}",
            "generation": generation,
            "created_at": time.time(),
            "window": window,
            "capture": capture,
            "hints": {h["id"]: {k: h[k] for k in
                                ("x", "y", "name", "type", "bounds",
                                 "hwnd", "enabled") if k in h}
                      for h in hints}}
    tmp = sidecar_path() + f".{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, sidecar_path())
    return data


def hint_count():
    """Number of hints in the current sidecar — the choice count Hick–Hyman
    pre-click delay scales on. None when no observation exists."""
    d = _read_sidecar()
    return len(d["hints"]) if d and d.get("hints") else None


def invalidate_sidecar():
    """Drop all outstanding hints — e.g. when a capture fell back to grid."""
    try:
        os.remove(sidecar_path())
    except OSError:
        pass


def _window_alive(hwnd):
    if not hwnd or os.name != "nt":
        return True
    import ctypes
    return bool(ctypes.windll.user32.IsWindow(hwnd))


def window_foreground(hwnd):
    """Is hwnd the foreground window? Physical keystrokes land on whatever
    has focus — callers targeting a specific window must gate on this."""
    if not hwnd or os.name != "nt":
        return True
    import ctypes
    return ctypes.windll.user32.GetForegroundWindow() == hwnd


def resolve_hint(hint_id, session=None, generation=None):
    """Return (entry, reason). entry has x, y, name, type, bounds, hwnd,
    enabled; reason is None on success, else a typed staleness code —
    callers must NOT dispatch input when reason is set. Pass `generation`
    (the observation's generation) to reject hints minted before a newer
    re-observation — plain ids alone are ambiguous across snapshots."""
    data = _read_sidecar()
    if data is None:
        return None, "no_sidecar"
    if data.get("schema_version") != SCHEMA_VERSION:
        return None, "schema"
    if session is not None and data.get("session_id") != session:
        return None, "session"
    if generation is not None and data.get("generation") != generation:
        return None, "stale_generation"
    if time.time() - data.get("created_at", 0) > HINT_TTL_S:
        return None, "expired"
    e = data.get("hints", {}).get(str(hint_id).lower())
    if not e:
        return None, "unknown_hint"
    if not _window_alive(e.get("hwnd")):
        return None, "window_gone"
    return e, None
