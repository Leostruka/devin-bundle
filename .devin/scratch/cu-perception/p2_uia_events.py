#!/usr/bin/env python3
"""P2 probe: UIA client event handlers as semantic wake channel.

comtypes COMObject handlers on a dedicated MTA thread (per MS threading
guidance). Registers:
  - StructureChanged on desktop root, TreeScope_Children (window spawn)
  - PropertyChanged [Name, BoundingRectangle] on target element
Both with a CacheRequest prefetching Name+Bounds+ControlType so the
sender element arrives with properties (verifies prefetch == zero extra
RPC by reading Cached* on receipt).

wake_ms = consumer stamp (perf_counter == QPC epoch) minus trigger QPC
printed by the third-process helper (p1_target --qpc / p1_rename).

Output: JSON per-channel summaries.
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import queue
import statistics
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TRIALS = int(sys.argv[sys.argv.index("--trials") + 1]) \
    if "--trials" in sys.argv else 10

events_q = queue.Queue()
stop_ev = threading.Event()
err = {}

import comtypes
import comtypes.client

comtypes.client.GetModule("UIAutomationCore.dll")
import comtypes.gen.UIAutomationClient as uia_tlb

UIA_NamePropertyId = 30005
UIA_BoundingRectanglePropertyId = 30001
UIA_ControlTypePropertyId = 30003
TreeScope_Element = 0x1
TreeScope_Children = 0x2


def _stamp(tag, **kw):
    events_q.put((time.perf_counter(), tag, kw))


class StructHandler(comtypes.COMObject):
    _com_interfaces_ = [uia_tlb.IUIAutomationStructureChangedEventHandler]

    def HandleStructureChangedEvent(self, sender, change_type, runtime_id):
        _stamp("structure", change=change_type)


class PropHandler(comtypes.COMObject):
    _com_interfaces_ = [uia_tlb.IUIAutomationPropertyChangedEventHandler]

    def HandlePropertyChangedEvent(self, sender, prop, value):
        name = None
        try:
            name = sender.CachedName
        except Exception:
            pass
        _stamp("prop", prop=prop, cached_name=name)


class FocusHandler(comtypes.COMObject):
    _com_interfaces_ = [uia_tlb.IUIAutomationFocusChangedEventHandler]

    def HandleFocusChangedEvent(self, sender):
        _stamp("focus")


def worker(hwnd, ready_ev):
    """Whole UIA lifecycle inside one MTA thread."""
    try:
        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        uia = comtypes.client.CreateObject(
            "{ff48dba4-60ef-4201-aa87-54103eef594e}",
            interface=uia_tlb.IUIAutomation)
        root = uia.GetRootElement()
        target = uia.ElementFromHandle(hwnd)

        req = uia.CreateCacheRequest()
        req.AddProperty(UIA_NamePropertyId)
        req.AddProperty(UIA_BoundingRectanglePropertyId)
        req.AddProperty(UIA_ControlTypePropertyId)

        sh, ph, fh = StructHandler(), PropHandler(), FocusHandler()
        uia.AddStructureChangedEventHandler(
            root, TreeScope_Children, req, sh)
        uia.AddPropertyChangedEventHandler(
            target, TreeScope_Element, req, ph,
            (UIA_NamePropertyId, UIA_BoundingRectanglePropertyId))
        try:
            uia.AddFocusChangedEventHandler(req, fh)
        except Exception as e:
            err["focus_register"] = repr(e)
        ready_ev.set()

        while not stop_ev.wait(0.05):
            pass
        uia.RemoveAllEventHandlers()
    except Exception as e:
        err["worker"] = repr(e)
        ready_ev.set()
    finally:
        comtypes.CoUninitialize()


def find_window(substr, timeout=15):
    u = ctypes.windll.user32
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def en(h, l):
        if u.IsWindowVisible(h):
            n = u.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(h, b, n + 1)
                out.append((h, b.value))
        return True

    dl = time.time() + timeout
    while time.time() < dl:
        out.clear()
        u.EnumWindows(en, 0)
        for h, t in out:
            if substr in t:
                return h
        time.sleep(0.1)
    return None


def spawn_target(marker):
    """Returns (proc, qpc_seconds_before_create)."""
    p = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "p1_target.py"),
         marker, "60", "--qpc"],
        stdout=subprocess.PIPE, text=True)
    line = p.stdout.readline().split()
    return p, int(line[0]) / int(line[1])


def flush(q):
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            return


def drain(q, tag, timeout=4.0, pred=None):
    dl = time.time() + timeout
    while time.time() < dl:
        try:
            e = q.get(timeout=max(0.01, dl - time.time()))
        except queue.Empty:
            break
        if e[1] == tag and (pred is None or pred(e)):
            return e
    return None


def summ(v):
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "p50": round(statistics.median(v), 3),
            "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 3),
            "min": round(min(v), 3), "max": round(max(v), 3)}


def main():
    marker0 = f"cu_p2_{int(time.time())}"
    proc, t_create = spawn_target(marker0)
    hwnd = find_window(marker0)
    if not hwnd:
        print(json.dumps({"ok": False, "error": "no target"}))
        proc.kill()
        return

    ready = threading.Event()
    t = threading.Thread(target=worker, args=(hwnd, ready), daemon=True)
    t.start()
    ready.wait(10)
    if "worker" in err:
        print(json.dumps({"ok": False, "error": err["worker"]}))
        proc.kill()
        return

    res = {"structure_spawn_ms": [], "prop_name_ms": [],
           "prop_cached_name_ok": 0, "prop_name_events": 0,
           "focus_events": 0}
    flush(events_q)
    time.sleep(0.3)

    # A) spawn -> StructureChanged on root children
    for i in range(TRIALS):
        p2, t0 = spawn_target(f"{marker0}_s{i}")
        ev = drain(events_q, "structure", timeout=6)
        if ev:
            res["structure_spawn_ms"].append(round((ev[0] - t0) * 1000, 2))
        p2.kill()

    # B) foreign rename -> PropertyChanged(Name) on target element
    for i in range(TRIALS):
        rp = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "p1_rename.py"),
             str(hwnd), f"{marker0}_n{i}"],
            stdout=subprocess.PIPE, text=True)
        line = rp.stdout.readline().split()
        t0 = int(line[0]) / int(line[1])
        ev = drain(events_q, "prop", timeout=4,
                   pred=lambda e: e[2].get("prop") == UIA_NamePropertyId)
        res["prop_name_events"] += 1 if ev else 0
        if ev:
            res["prop_name_ms"].append(round((ev[0] - t0) * 1000, 2))
            if ev[2].get("cached_name"):
                res["prop_cached_name_ok"] += 1

    # C) focus burst check (ambient during trial run — count only)
    # SetForegroundWindow is lock-limited; count whatever arrived.
    time.sleep(0.2)
    while True:
        try:
            e = events_q.get_nowait()
            if e[1] == "focus":
                res["focus_events"] += 1
        except queue.Empty:
            break

    out = {"ok": True, "trials": TRIALS,
           "structure_spawn_ms": summ(res["structure_spawn_ms"]),
           "prop_name_ms": summ(res["prop_name_ms"]),
           "prop_name_events": res["prop_name_events"],
           "prop_cached_name_ok": res["prop_cached_name_ok"],
           "focus_events_seen": res["focus_events"],
           "errors": err}
    print(json.dumps(out, indent=1))
    stop_ev.set()
    t.join(5)
    proc.kill()


if __name__ == "__main__":
    main()
