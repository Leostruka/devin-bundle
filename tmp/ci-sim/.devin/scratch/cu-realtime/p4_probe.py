#!/usr/bin/env python3
"""P4 probes: resident UIA/DOM reflex loops + GUI cycle floor.

Run under the computer-use venv python:
  %APPDATA%\\devin\\extensions\\computer-use\\.venv\\Scripts\\python.exe p4_probe.py <mode>

Modes:
  uia-reflex  - spawn Notepad, resident enum poll detects the edit
                element, reflex uia_perform sets a value. Reports the
                honest decomposition: spawn->hwnd, hwnd->element,
                element->action.
  gui-cycle   - on the same Notepad: enum -> uia_perform(invoke "File")
                -> enum verifies menu items appeared -> post_key esc
                closes. One full perceive->act->verify in-process.
  dom-reflex  - spawn Edge with CDP on a local page, resident ws eval
                loop polls window.__appeared, clicks on appearance.
                Page-side performance.now() stamps give the true
                event->reaction latency.

Reflex safety: fixed action allowlist only (uia_perform on the matched
element inside the target hwnd; page eval click on #reflex-target),
max 1 action per run, poll cap, global deadline. No model in the loop.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = HERE.parents[2] / "extensions" / "computer-use"
sys.path.insert(0, str(EXT))

import cu_hints  # noqa: E402
import cu_scope  # noqa: E402

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PAGE = (HERE / "reflex_page.html").as_uri()
POLL_S = 0.05
DEADLINE_S = 20.0


def _enum_hwnd(hwnd):
    """Per-window enum: same path as enum_clickables but addressed by
    hwnd (public API only exposes focused|all). Returns element dicts
    with _el stripped."""
    res = cu_hints._com_thread(lambda: cu_hints._enum_impl("all", hwnd))
    if not res:
        return []
    els, _win = res
    return els or []


def _notepad_hwnds():
    return {w["hwnd"] for w in
            (cu_scope.find_windows(class_name="Notepad") or [])}


def _find_notepad(pre_hwnds, deadline, pred=None):
    """Win11 Notepad is UWP: the spawned pid is a stub and the app owns
    TWO class-Notepad hwnds (tab-strip frame vs content). pred picks
    the one whose enum contains the element we need."""
    pred = pred or (lambda els: _pick_edit(els) is not None)
    while time.monotonic() < deadline:
        for h in _notepad_hwnds() - pre_hwnds:
            if pred(_enum_hwnd(h)):
                return h
        time.sleep(POLL_S)
    return None


def els_have_edit(hwnd):
    return _pick_edit(_enum_hwnd(hwnd)) is not None


def _close_hwnd(hwnd):
    """WM_CLOSE the window we opened — the UWP stub pid is already
    gone, terminate() would never reach the real Notepad."""
    try:
        cu_scope._post(hwnd, 0x0010, 0, 0)
    except Exception:
        pass


def _pick_edit(els):
    """The deterministic reflex target: Notepad's 'Add New Tab' button.
    Provider elements carry hwnd:null, so uia_perform (entry re-resolve)
    cannot act on them — the uia channel addresses by window+name."""
    for e in els:
        if (e.get("name") or "") == "Add New Tab" and e.get("enabled"):
            return e
    return None


def uia_reflex():
    """spawn -> resident enum poll -> uia set_value, one action."""
    pre = _notepad_hwnds()
    t0 = time.monotonic()
    proc = subprocess.Popen(["notepad.exe"])
    hwnd = None
    edit = None
    poll_ms = []
    t_hwnd = t_el = None
    seen_hwnd = False
    while time.monotonic() - t0 < DEADLINE_S:
        new = _notepad_hwnds() - pre
        if new and not seen_hwnd:
            seen_hwnd = True
            t_hwnd = time.monotonic()
        for h in new:
            pt = time.monotonic()
            els = _enum_hwnd(h)
            poll_ms.append((time.monotonic() - pt) * 1000)
            edit = _pick_edit(els)
            if edit:
                hwnd = h
                t_el = time.monotonic()
                break
        if edit:
            break
        time.sleep(POLL_S)
    if not (hwnd and edit):
        for h in _notepad_hwnds() - pre:
            _close_hwnd(h)
        return {"ok": False, "stage": "detect",
                "hwnd": hwnd, "edit": bool(edit)}
    t_a = time.monotonic()
    res = cu_scope.uia_invoke(hwnd, name="Add New Tab")
    t_done = time.monotonic()
    ok = isinstance(res, dict) and not res.get("error")
    out = {"ok": ok, "action": res,
           "spawn_to_hwnd_ms": round((t_hwnd - t0) * 1000, 1)
           if t_hwnd else None,
           "hwnd_to_element_ms": round((t_el - t_hwnd) * 1000, 1),
           "element_to_action_ms": round((t_done - t_a) * 1000, 1),
           "event_to_action_ms": round((t_done - t0) * 1000, 1),
           "poll_ms_p50": sorted(poll_ms)[len(poll_ms) // 2]
           if poll_ms else None,
           "polls": len(poll_ms)}
    _close_hwnd(hwnd)
    return out


def gui_cycle(hwnd):
    """enum -> invoke File -> enum verifies menu -> esc. Times per phase."""
    ph = {}
    deadline = time.monotonic() + 5
    els = []
    while time.monotonic() < deadline:
        els = _enum_hwnd(hwnd)
        if any((e.get("name") or "") == "File" for e in els):
            break
        time.sleep(POLL_S)
    t = time.monotonic()
    els = _enum_hwnd(hwnd)
    ph["perceive_ms"] = (time.monotonic() - t) * 1000
    file_el = next((e for e in els
                    if (e.get("name") or "").lower() == "file"
                    and (e["type"] or "").lower() in
                    ("menuitem", "button", "splitbutton", "menu")), None)
    if file_el is None:
        cands = {e["type"]: e.get("name") for e in els}
        return {"ok": False, "stage": "no_file_el", "cands": cands}
    t = time.monotonic()
    res = cu_scope.uia_invoke(hwnd, name="File")
    ph["act_ms"] = (time.monotonic() - t) * 1000
    if not isinstance(res, dict) or res.get("error"):
        return {"ok": False, "stage": "invoke", "res": res}
    t = time.monotonic()
    ok = False
    for _ in range(40):
        els2 = _enum_hwnd(hwnd)
        names = {(e.get("name") or "").lower() for e in els2}
        if {"new", "open"} & names or any("save" in n for n in names):
            ok = True
            break
        time.sleep(POLL_S)
    ph["verify_ms"] = (time.monotonic() - t) * 1000
    cu_scope.post_key(hwnd, "esc")
    ph["total_ms"] = sum(ph[k] for k in
                         ("perceive_ms", "act_ms", "verify_ms"))
    ph = {k: round(v, 1) for k, v in ph.items()}
    ph["ok"] = ok
    return ph


def dom_reflex():
    """Resident ws eval loop: poll __appeared -> click -> __hit."""
    import cu_browser
    prof = HERE / "edge-profile"
    prof.mkdir(exist_ok=True)
    proc = subprocess.Popen([
        EDGE, "--remote-debugging-port=9222",
        f"--user-data-dir={prof}", "--no-first-run",
        "--no-default-browser-check", PAGE])
    try:
        bind = subprocess.run(
            [sys.executable, str(EXT / "browser.py"), "bind",
             "--endpoint", "http://127.0.0.1:9222",
             "--pid", str(proc.pid)],
            capture_output=True, text=True, timeout=20)
        if '"ok": true' not in bind.stdout:
            return {"ok": False, "stage": "bind", "out": bind.stdout,
                    "err": bind.stderr[-300:]}
        # /json/list holds many page targets (extensions, new tab) —
        # attach to OUR page by URL, not the first page found.
        ws_url = None
        for _ in range(40):
            pages = cu_browser._http_json(
                "http://127.0.0.1:9222/json/list") or []
            hit = next((t for t in pages
                        if t.get("type") == "page"
                        and "reflex_page" in (t.get("url") or "")
                        and t.get("webSocketDebuggerUrl")), None)
            if hit:
                ws_url = hit["webSocketDebuggerUrl"]
                break
            time.sleep(0.25)
        if ws_url is None:
            return {"ok": False, "stage": "no_page_target"}
        ws = cu_browser._WSClient(ws_url, "cdp", 30.0)

        def ev(expr):
            r = ws.call("Runtime.evaluate",
                        {"expression": expr, "returnByValue": True})
            # ws.call already unwraps to the command's result object:
            # Runtime.evaluate -> {"result": RemoteObject} — value is
            # one level down, not two.
            return (r.get("result") or {}).get("value")

        ev("window.__arm(800)")
        t0 = time.monotonic()
        poll_ms = []
        hit = None
        while time.monotonic() - t0 < 10:
            pt = time.monotonic()
            st = json.loads(ev("window.__state()") or "{}")
            poll_ms.append((time.monotonic() - pt) * 1000)
            if st.get("a") and not st.get("h"):
                t_click = time.monotonic()
                ev("document.getElementById('reflex-target').click()")
                t_done = time.monotonic()
                time.sleep(0.05)
                st = json.loads(ev("window.__state()") or "{}")
                hit = {"event_to_reaction_ms":
                       round(st["h"] - st["a"], 1),
                       "click_dispatch_ms":
                       round((t_done - t_click) * 1000, 1),
                       "appeared_wall_ms":
                       round((t_click - t0) * 1000, 1),
                       "poll_ms_p50":
                       sorted(poll_ms)[len(poll_ms) // 2],
                       "polls": len(poll_ms)}
                break
            time.sleep(POLL_S)
        ws.close()
        if hit is None:
            return {"ok": False, "stage": "timeout",
                    "polls": len(poll_ms)}
        hit["ok"] = True
        return hit
    finally:
        # kill the whole tree — terminate() only hits the launcher
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "uia-reflex"
    if mode == "dom-reflex":
        out = dom_reflex()
    elif mode == "uia-reflex":
        out = uia_reflex()
    elif mode == "gui-cycle":
        pre = _notepad_hwnds()
        proc = subprocess.Popen(["notepad.exe"])
        try:
            hwnd = _find_notepad(
                pre, time.monotonic() + DEADLINE_S,
                pred=lambda els: any(
                    (e.get("name") or "") == "File" for e in els))
            out = (gui_cycle(hwnd) if hwnd
                   else {"ok": False, "stage": "no_hwnd"})
            if hwnd:
                _close_hwnd(hwnd)
        finally:
            proc.terminate()
    else:
        out = {"ok": False, "error": f"unknown mode {mode}"}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
