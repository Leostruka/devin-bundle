#!/usr/bin/env python3
"""P11 probe: event-driven hint refresh — the daemon loop end-to-end.

Simulates the production design: WinEvent hook (out-of-context, pump
thread) -> hwnd/event filter -> cu_hints enum on the affected window ->
hint-set refreshed. Measures event->refreshed-hints latency vs the
591ms cold `screenshot --hints` CLI baseline and UIA enum baselines.
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
sys.path.insert(0, os.path.join(HERE, "..", "..", "..",
                                  "extensions", "computer-use"))

import cu_hints  # noqa: E402

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_CREATE = 0x8000
EVENT_OBJECT_SHOW = 0x8002
EVENT_OBJECT_DESTROY = 0x8001
EVENT_OBJECT_LOCATIONCHANGE = 0x800B
EVENT_OBJECT_NAMECHANGE = 0x800C
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002
WM_QUIT = 0x0012
WINEVENTPROC = ctypes.WINFUNCTYPE(
    None, wt.HANDLE, wt.DWORD, wt.HWND, wt.LONG, wt.LONG,
    wt.DWORD, wt.DWORD)

REFRESH_EVENTS = {EVENT_OBJECT_CREATE, EVENT_OBJECT_SHOW,
                  EVENT_OBJECT_LOCATIONCHANGE, EVENT_OBJECT_NAMECHANGE}
TRIALS = int(sys.argv[sys.argv.index("--trials") + 1]) \
    if "--trials" in sys.argv else 8


class HookThread(threading.Thread):
    def __init__(self, q):
        super().__init__(daemon=True)
        self.q = q
        self.ready = threading.Event()
        self.tid = None

    def run(self):
        self.tid = kernel32.GetCurrentThreadId()

        def _cb(hook, event, hwnd, id_obj, id_child, tid, ms):
            self.q.put((time.perf_counter(), event, int(hwnd or 0)))

        self._cb = WINEVENTPROC(_cb)
        hooks = []
        for lo, hi in ((EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND),
                       (EVENT_OBJECT_CREATE, EVENT_OBJECT_NAMECHANGE)):
            h = user32.SetWinEventHook(
                lo, hi, None, self._cb, 0, 0,
                WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS)
            if h:
                hooks.append(h)
        self.ready.set()
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        for h in hooks:
            user32.UnhookWinEvent(h)

    def stop(self):
        user32.PostThreadMessageW(self.tid, WM_QUIT, 0, 0)


def find_window(substr, timeout=15):
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def en(h, l):
        if user32.IsWindowVisible(h):
            n = user32.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(h, b, n + 1)
                out.append((h, b.value))
        return True

    dl = time.time() + timeout
    while time.time() < dl:
        out.clear()
        user32.EnumWindows(en, 0)
        for h, t in out:
            if substr in t:
                return h
        time.sleep(0.1)
    return None


def enum_hwnd(hwnd, timeout=6.0):
    """enum_clickables for a specific hwnd via the same COM worker."""
    q = queue.Queue(maxsize=1)

    def work():
        els, win = cu_hints._enum_impl("x", hwnd=hwnd)
        q.put((els, win))

    t = threading.Thread(target=lambda: cu_hints._com_thread(work),
                         daemon=True)
    t.start()
    try:
        return q.get(timeout=timeout)
    except queue.Empty:
        return [], None


def summ(v):
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "p50": round(statistics.median(v), 3),
            "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 3)}


def main():
    rep = {"ok": True}
    q = queue.Queue()
    hook = HookThread(q)
    hook.start()
    hook.ready.wait(5)

    stats = {"events": 0, "triggered": 0, "skipped": 0}

    def drain_to(pred, timeout=5.0):
        """Wait for matching event; count filtered noise meanwhile."""
        dl = time.time() + timeout
        while time.time() < dl:
            try:
                e = q.get(timeout=max(0.01, dl - time.time()))
                stats["events"] += 1
                if pred(e):
                    stats["triggered"] += 1
                    return e
                stats["skipped"] += 1
            except queue.Empty:
                break
        return None

    # warm UIA once (engine init cost not the subject)
    els0, _ = enum_hwnd(user32.GetForegroundWindow())

    # A) new window spawn -> CREATE/SHOW -> enum that hwnd
    spawn_lat, spawn_hints = [], []
    for _ in range(TRIALS):
        marker = f"cu_p11_{int(time.time()*1000)%100000}"
        proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "p1_target.py"),
             marker, "30", "--drawtext"])
        hwnd = find_window(marker, timeout=8)
        ev = drain_to(
            lambda e: e[1] in (EVENT_OBJECT_SHOW, EVENT_OBJECT_CREATE)
            and e[2] == hwnd, timeout=8) if hwnd else None
        if ev:
            t0 = time.perf_counter()
            els, win = enum_hwnd(ev[2])
            dt = (time.perf_counter() - t0) * 1000
            spawn_lat.append((ev[0], dt))
            spawn_hints.append(len(els))
        proc.kill()
        time.sleep(0.3)
    if spawn_lat:
        # end-to-end = event arrival -> hints ready = enum cost (event ts
        # precedes our drain find; report enum latency + count)
        rep["spawn_enum_ms"] = summ([d for _, d in spawn_lat])
        rep["spawn_hints"] = spawn_hints

    # B) LOCATIONCHANGE on stable window -> re-enum
    marker = f"cu_p11s_{int(time.time())}"
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "p1_target.py"),
         marker, "60", "--drawtext", "--topmost"])
    hwnd = find_window(marker)
    rep["target_hwnd"] = hwnd
    loc_ms, loc_hints = [], []
    if hwnd:
        enum_hwnd(hwnd)  # initial index
        for i in range(TRIALS):
            r = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            user32.SetWindowPos(hwnd, None, r.left + 20, r.top,
                                0, 0, 0x0001 | 0x0004 | 0x0010)
            ev = drain_to(
                lambda e: e[1] == EVENT_OBJECT_LOCATIONCHANGE
                and e[2] == hwnd, timeout=4)
            if ev:
                # daemon cost = event->refresh; event ts approximates
                # trigger (move issued ~just before drain)
                t_ev = ev[0]
                els, win = enum_hwnd(ev[2])
                dt = (time.perf_counter() - t_ev) * 1000
                loc_ms.append(dt)
                loc_hints.append(len(els))
            time.sleep(0.25)
    rep["move_event_to_hints_ms"] = summ(loc_ms)
    rep["move_hints"] = loc_hints

    # C) ambient noise during a 3s idle + activity window
    n0 = stats["events"]
    time.sleep(3.0)
    while True:
        try:
            q.get_nowait()
            stats["events"] += 1
        except queue.Empty:
            break
    rep["ambient_events_3s"] = stats["events"] - n0
    rep["stats"] = stats

    print(json.dumps(rep, indent=1))
    hook.stop()
    proc.kill()


if __name__ == "__main__":
    main()
