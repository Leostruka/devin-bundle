#!/usr/bin/env python3
"""P1 probe: WinEvents (SetWinEventHook out-of-context) as wake channel.

Measures, per event type, wake_ms = consumer-notified time minus trigger
time, on FOREIGN windows (cross-process marshaling included). Compares
against an equivalent cheap poll (GetWindowRect @ 50Hz) for the same
change. Stdlib ctypes only.

Trigger actions the probe performs itself on a spawned console window
(foreign process) so t0 is exact:
  LOCATIONCHANGE  SetWindowPos +-1px (reversible)
  NAMECHANGE      SetWindowTextW
Lower bound: own-process window (same-process event generation).

Output: JSON {wake_ms: {type: {n,p50,p95,min,max}}, ...}.
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

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WINEVENTPROC = ctypes.WINFUNCTYPE(
    None, wt.HANDLE, wt.DWORD, wt.HWND, wt.LONG, wt.LONG, wt.DWORD, wt.DWORD)

EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_CREATE = 0x8000
EVENT_OBJECT_LOCATIONCHANGE = 0x800B
EVENT_OBJECT_NAMECHANGE = 0x800C
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
WM_QUIT = 0x0012

CREATE_NEW_CONSOLE = 0x00000010
EVENT_COUNTS = {}


class HookThread(threading.Thread):
    """Dedicated pump thread: hook install + GetMessage loop must live on
    the same thread; UnhookWinEvent must also run here."""

    def __init__(self, events_q, skip_own=True):
        super().__init__(daemon=True)
        self.q = events_q
        self.skip_own = skip_own
        self.ready = threading.Event()
        self.tid = None

    def run(self):
        self.tid = kernel32.GetCurrentThreadId()
        flags = WINEVENT_OUTOFCONTEXT
        if self.skip_own:
            flags |= WINEVENT_SKIPOWNPROCESS

        def _cb(hook, event, hwnd, id_obj, id_child, tid, ms):
            self.q.put((time.perf_counter(), event, int(hwnd or 0),
                        id_obj, id_child))
            EVENT_COUNTS[hex(event)] = EVENT_COUNTS.get(hex(event), 0) + 1

        self._cb = WINEVENTPROC(_cb)  # keep alive for hook lifetime
        hooks = []
        for lo, hi in ((EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND),
                       (EVENT_OBJECT_CREATE, EVENT_OBJECT_NAMECHANGE)):
            h = user32.SetWinEventHook(lo, hi, None, self._cb, 0, 0, flags)
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


def find_window_by_title(substr, timeout=10.0):
    """First visible top-level hwnd whose title contains substr."""
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def _enum(hwnd, lp):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                out.append((hwnd, buf.value))
        return True

    deadline = time.time() + timeout
    while time.time() < deadline:
        out.clear()
        user32.EnumWindows(_enum, 0)
        for hwnd, title in out:
            if substr.lower() in title.lower():
                return hwnd
        time.sleep(0.1)
    return None


def window_rect(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def drain_matching(q, event, hwnd, timeout=3.0):
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            e = q.get(timeout=max(0.01, deadline - time.time()))
            if e[1] == event and e[2] == hwnd:
                return e
    except queue.Empty:
        pass
    return None


def poll_detect(hwnd, old_rect, timeout=1.0, interval=0.02):
    """Cheap-equivalent poll: GetWindowRect at `interval` until change."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        if window_rect(hwnd) != old_rect:
            return (time.perf_counter() - t0) * 1000.0
        time.sleep(interval)
    return None


def flush(q):
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            return


def summ(v):
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "p50": round(statistics.median(v), 3),
            "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 3),
            "min": round(min(v), 3), "max": round(max(v), 3)}


def main():
    trials = int(sys.argv[sys.argv.index("--trials") + 1]) \
        if "--trials" in sys.argv else 10
    q = queue.Queue()
    hook = HookThread(q, skip_own=True)
    hook.start()
    hook.ready.wait(5)

    marker = f"cu_p1_{int(time.time())}"
    here = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.Popen(
        [sys.executable, os.path.join(here, "p1_target.py"),
         marker, "120"])
    hwnd = find_window_by_title(marker, timeout=15)
    results = {"location_foreign": [], "name_foreign": [],
               "poll_location": [], "own_location": []}

    if hwnd is None:
        print(json.dumps({"ok": False, "error": "console window not found"}))
        hook.stop()
        proc.kill()
        return

    # settle + drain pre-existing events
    time.sleep(0.5)
    flush(q)

    for i in range(trials):
        # LOCATIONCHANGE: +-1px, reversible
        rect = window_rect(hwnd)
        dx = 1 if i % 2 == 0 else -1
        t0 = time.perf_counter()
        ok = user32.SetWindowPos(hwnd, None, rect[0] + dx, rect[1], 0, 0,
                                 SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
        if not ok:
            results.setdefault("setwindowpos_fail",
                               kernel32.GetLastError())
        ev = drain_matching(q, EVENT_OBJECT_LOCATIONCHANGE, hwnd)
        if ev:
            results["location_foreign"].append(
                round((ev[0] - t0) * 1000.0, 3))

        # poll comparison on the reverse move
        rect = window_rect(hwnd)
        ok2 = user32.SetWindowPos(hwnd, None, rect[0] - dx, rect[1], 0, 0,
                                  SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
        if not ok2:
            results.setdefault("setwindowpos_fail",
                               kernel32.GetLastError())
        pd = poll_detect(hwnd, rect, timeout=1.0)
        drain_matching(q, EVENT_OBJECT_LOCATIONCHANGE, hwnd, timeout=0.5)
        if pd is not None:
            results["poll_location"].append(round(pd, 3))

        # NAMECHANGE: renamed by a THIRD process so the event is
        # foreign-generated (SKIPOWNPROCESS drops events our own calls
        # trigger). Helper prints its QPC stamp before SetWindowTextW.
        rp = subprocess.Popen(
            [sys.executable, os.path.join(here, "p1_rename.py"),
             str(hwnd), f"{marker}_{i}"],
            stdout=subprocess.PIPE, text=True)
        line = rp.stdout.readline().split()
        qpc_set, qpc_freq = int(line[0]), int(line[1])
        ev = drain_matching(q, EVENT_OBJECT_NAMECHANGE, hwnd)
        if ev:
            # perf_counter() on Windows is QueryPerformanceCounter/freq —
            # same clock and epoch as the helper's raw QPC stamp.
            results["name_foreign"].append(
                round((ev[0] - qpc_set / qpc_freq) * 1000.0, 3))
        else:
            results.setdefault("name_miss_seen", []).append("miss")

    # idle noise: 3s listening with no triggers
    flush(q)
    time.sleep(3.0)
    noise = 0
    while True:
        try:
            q.get_nowait()
            noise += 1
        except queue.Empty:
            break
    results["idle_noise_events_3s"] = noise

    # own-process lower bound: ctypes-created window, no skip flag
    q2 = queue.Queue()
    hook2 = HookThread(q2, skip_own=False)
    hook2.start()
    hook2.ready.wait(5)
    WNDPROC = ctypes.WINFUNCTYPE(
        wt.LPARAM, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [("cbSize", wt.UINT), ("style", wt.UINT),
                    ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE),
                    ("hIcon", wt.HICON), ("hCursor", wt.HCURSOR),
                    ("hbrBackground", wt.HBRUSH),
                    ("lpszMenuName", wt.LPCWSTR),
                    ("lpszClassName", wt.LPCWSTR), ("hIconSm", wt.HICON)]

    user32.DefWindowProcW.restype = wt.LPARAM
    user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT,
                                    wt.WPARAM, wt.LPARAM]

    def _wndproc(h, m, w, l):
        return user32.DefWindowProcW(h, m, w, l)

    _wndproc_cb = WNDPROC(_wndproc)
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(wc)
    wc.lpfnWndProc = _wndproc_cb
    wc.lpszClassName = "cu_p1_own"
    kernel32.GetModuleHandleW.restype = wt.HMODULE
    wc.hInstance = kernel32.GetModuleHandleW(None)
    user32.RegisterClassExW(ctypes.byref(wc))
    user32.CreateWindowExW.restype = wt.HWND
    own_hwnd = user32.CreateWindowExW(
        0, "cu_p1_own", "cu_p1_own", 0x08000000 | 0x10000000,
        100, 100, 200, 100, None, None, wt.HINSTANCE(wc.hInstance), None)
    time.sleep(0.3)
    flush(q2)
    for i in range(trials):
        rect = window_rect(own_hwnd)
        t0 = time.perf_counter()
        user32.SetWindowPos(own_hwnd, None, rect[0] + 1, rect[1], 0, 0,
                            SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
        ev = drain_matching(q2, EVENT_OBJECT_LOCATIONCHANGE, own_hwnd)
        if ev:
            results["own_location"].append(round((ev[0] - t0) * 1000.0, 3))
        msg = wt.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), own_hwnd, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    user32.DestroyWindow(own_hwnd)
    hook2.stop()

    diag = {k: v for k, v in results.items()
            if not isinstance(v, list) or k == "name_miss_seen"}
    out = {"ok": True, "trials": trials, "console_hwnd": hwnd,
           "idle_noise_events_3s": results["idle_noise_events_3s"],
           "diag": diag, "event_counts": EVENT_COUNTS,
           "wake_ms": {k: summ(v) for k, v in results.items()
                       if isinstance(v, list) and k != "name_miss_seen"}}
    print(json.dumps(out, indent=1))

    hook.stop()
    proc.kill()


if __name__ == "__main__":
    main()
