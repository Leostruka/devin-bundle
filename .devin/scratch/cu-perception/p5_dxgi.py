#!/usr/bin/env python3
"""P5 probe: DXGI Desktop Duplication via dxcam (scratch/_deps).

Measures:
  capture_ms  cam.grab() full + region vs mss baselines (28.1 / 6.9ms)
  acquire_ms  raw AcquireNextFrame(0) cost (what dxcam's update_frame pays)
  wake_ms     blocking AcquireNextFrame(timeout) return after a pixel
              change caused by a foreign window move (thread triggers at
              random delay while main blocks on the duplicator)
  present_lag info.LastPresentTime (QPC) minus trigger QPC — compositor
              -> frame-ready latency
  ambient     frame-arrival intervals on an idle desktop (spurious-wake
              rate for a blocking consumer)
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import statistics
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_deps"))

TRIALS = int(sys.argv[sys.argv.index("--trials") + 1]) \
    if "--trials" in sys.argv else 10

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


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


def summ(v):
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "p50": round(statistics.median(v), 3),
            "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 3),
            "min": round(min(v), 3), "max": round(max(v), 3)}


def main():
    import dxcam
    from dxcam._libs.dxgi import (DXGI_OUTDUPL_FRAME_INFO,
                                IDXGIResource)
    import comtypes

    WAIT_TIMEOUT = 0x887A0027

    def acquire(timeout_ms):
        """Raw AcquireNextFrame; returns (info, res) or 'timeout'/'error'."""
        info = DXGI_OUTDUPL_FRAME_INFO()
        res = ctypes.POINTER(IDXGIResource)()
        try:
            dup.AcquireNextFrame(timeout_ms, ctypes.byref(info),
                                 ctypes.byref(res))
        except comtypes.COMError as e:
            hr = e.args[0] & 0xFFFFFFFF if e.args else 0
            if hr == WAIT_TIMEOUT:
                return "timeout"
            if hr == 0x80004002:  # E_NOINTERFACE: event w/o desktop res
                try:
                    dup.ReleaseFrame()
                except comtypes.COMError:
                    pass
                return "nores"
            return f"err:0x{hr:08X}"
        return info, res

    def free(r):
        if isinstance(r, tuple):
            if r[1]:
                r[1].Release()
            try:
                dup.ReleaseFrame()
            except comtypes.COMError:
                pass

    def drain():
        n = 0
        for _ in range(100):
            r = acquire(0)
            if not isinstance(r, tuple):
                return n
            free(r)
            n += 1
        return n

    cam = dxcam.create(backend="dxgi", processor_backend="numpy",
                       output_color="RGB")
    rep = {"ok": True, "backend": "dxgi"}
    dup = cam._duplicator.duplicator  # IDXGIOutputDuplication COM ptr

    # capture_ms when a frame IS pending: move window, wait for the
    # frame, then time cam.grab() (acquire+stage copy+convert).
    marker = f"cu_p5_{int(time.time())}"
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "p1_target.py"),
         marker, "90", "--drawtext", "--topmost"])
    hwnd = find_window(marker)
    rep["target_hwnd"] = hwnd
    rep["target_visible"] = bool(hwnd and user32.IsWindowVisible(hwnd))

    def move_once():
        r = wt.RECT()
        ok = user32.GetWindowRect(hwnd, ctypes.byref(r))
        c = ctypes.c_int64()
        kernel32.QueryPerformanceCounter(ctypes.byref(c))
        t = c.value
        rc = user32.SetWindowPos(hwnd, None, r.left + 30, r.top,
                                 0, 0, 0x0001 | 0x0004 | 0x0400)
        return {"qpc": t, "swp": bool(rc), "rect": (r.left, r.top),
                "grc": bool(ok)}

    e2g, grab_dt = [], []
    for _ in range(6):
        drain()
        t0 = time.perf_counter()
        move_once()
        deadline = t0 + 4.0
        while time.perf_counter() < deadline:
            t1 = time.perf_counter()
            try:
                frame = cam.grab()
            except Exception:
                frame = None
            dt1 = (time.perf_counter() - t1) * 1000
            if frame is not None:
                e2g.append((time.perf_counter() - t0) * 1000)
                grab_dt.append(dt1)
                break
            time.sleep(0.001)
        time.sleep(0.15)
    rep["event_to_grab_ms"] = summ(e2g)
    rep["grab_pending_cost_ms"] = summ(grab_dt)

    # wake_ms: drain queue, main blocks on AcquireNextFrame(5000),
    # thread moves the foreign window at a random delay.
    wake, lag, acc = [], [], []
    move_diag = []
    if hwnd:
        for i in range(TRIALS):
            drain()
            delay = 0.3 + (i % 5) * 0.13
            trig = {"m": None}

            def _move():
                time.sleep(delay)
                trig["m"] = move_once()

            th = threading.Thread(target=_move, daemon=True)
            t_block0 = time.perf_counter()
            th.start()
            r = acquire(5000)
            t_ret = time.perf_counter()
            th.join()
            freq = cam._duplicator.performance_frequency
            m = trig["m"]
            move_diag.append(m)
            if isinstance(r, tuple) and m:
                ttrig = m["qpc"] / freq
                wake.append((t_ret - ttrig) * 1000)
                lag.append((int(r[0].LastPresentTime) / freq
                            - ttrig) * 1000)
                acc.append(int(r[0].AccumulatedFrames))
                free(r)
            elif r == "nores" and m:
                wake.append((t_ret - m["qpc"] / freq) * 1000)
                move_diag[-1]["acquire"] = "nores"
            elif not isinstance(r, tuple):
                move_diag[-1]["acquire"] = r
            time.sleep(0.15)
    rep["wake_ms"] = summ(wake)
    rep["present_lag_ms"] = summ(lag)
    rep["accumulated_frames"] = acc
    rep["move_diag"] = move_diag

    # drain stats + ambient: frame-arrival intervals, idle desktop, 3s
    intervals = []
    t_prev = None
    t_end = time.perf_counter() + 3.0
    while time.perf_counter() < t_end:
        r = acquire(300)
        if isinstance(r, tuple):
            now = time.perf_counter()
            if t_prev is not None:
                intervals.append(round((now - t_prev) * 1000, 2))
            t_prev = now
            free(r)
        elif r == "nores":
            now = time.perf_counter()
            if t_prev is not None:
                intervals.append(round((now - t_prev) * 1000, 2))
            t_prev = now
        elif r != "timeout":
            break
    rep["ambient_frame_intervals_ms"] = intervals[:20]
    rep["ambient_count_3s"] = len(intervals) + (1 if t_prev else 0)

    print(json.dumps(rep, indent=1))
    if hwnd:
        proc.kill()
    try:
        cam.release()
    except Exception:
        pass


if __name__ == "__main__":
    main()
