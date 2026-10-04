#!/usr/bin/env python3
"""P3 probe: coordinate-space precision.

1) Reports process DPI awareness before/after upgrade to
   PER_MONITOR_AWARE_V2 (SetProcessDpiAwarenessContext(-4)).
2) Audits physical-vs-logical: GetWindowRect vs
   DWMWA_EXTENDED_FRAME_BOUNDS vs monitor DPI for top windows;
   GetCursorPos vs GetPhysicalCursorPos.
3) ElementFromPoint round-trip: for every clickable element of the
   focused window (extension cu_hints enum), ElementFromPoint(center)
   must hit the same element or a descendant/ancestor of it — the
   production click model. Reports hit rate and center offsets.

Uses the extension venv (comtypes). ctypes + extension modules only.
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import sys
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shcore = ctypes.windll.shcore
dwmapi = ctypes.windll.dwmapi

EXT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "extensions",
    "computer-use"))
sys.path.insert(0, EXT)

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
DWMWA_EXTENDED_FRAME_BOUNDS = 9


def awareness_label():
    """GetAwarenessFromDpiAwarenessContext(GetThreadDpiAwarenessContext)."""
    try:
        ctx = user32.GetThreadDpiAwarenessContext()
        a = user32.GetAwarenessFromDpiAwarenessContext(ctx)
        # returns DPI_AWARENESS: -1 invalid, 0 unaware, 1 system, 2 per-monitor
        return int(a), int(ctx) if isinstance(ctx, int) else ctx
    except Exception as e:
        return None, repr(e)


def rect_of(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def dwm_frame(hwnd):
    r = wt.RECT()
    hr = dwmapi.DwmGetWindowAttribute(
        hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(r),
        ctypes.sizeof(r))
    return (r.left, r.top, r.right, r.bottom) if hr == 0 else None


def enum_windows():
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def en(h, l):
        if user32.IsWindowVisible(h):
            out.append(h)
        return True

    user32.EnumWindows(en, 0)
    return out


def main():
    report = {"awareness_before": awareness_label()[0]}
    user32.SetProcessDpiAwarenessContext(
        ctypes.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2))
    report["awareness_after_v2"] = awareness_label()[0]

    # system + per-monitor DPI sample
    report["dpi_system"] = user32.GetDpiForSystem()
    wins = enum_windows()
    audit = []
    for h in wins[:60]:
        gr, df = rect_of(h), dwm_frame(h)
        if df is None:
            continue
        dpi = user32.GetDpiForWindow(h)
        # if DWM bounds (physical truth) differ from GetWindowRect, the
        # latter is virtualized or includes invisible resize borders
        audit.append({"hwnd": int(h), "dpi": dpi,
                      "gwr": gr, "dwm": df,
                      "delta_l": gr[0] - df[0], "delta_r": gr[2] - df[2]})
    diff = [a for a in audit if a["delta_l"] or a["delta_r"]]
    report["rect_audit_n"] = len(audit)
    report["rect_mismatch_n"] = len(diff)
    report["rect_mismatch_sample"] = diff[:5]
    report["dpi_values"] = sorted({a["dpi"] for a in audit})

    cp, pp = wt.POINT(), wt.POINT()
    user32.GetCursorPos(ctypes.byref(cp))
    try:
        user32.GetPhysicalCursorPos(ctypes.byref(pp))
        report["cursor_logical_vs_physical"] = [
            (cp.x, cp.y), (pp.x, pp.y)]
    except Exception as e:
        report["cursor_physical_err"] = repr(e)

    # ElementFromPoint round-trip on focused window's clickables
    if "--notepad" in sys.argv:
        import subprocess
        np_proc = subprocess.Popen(["notepad.exe"])
        time.sleep(2.5)  # UWP takes focus + builds UI
    import cu_hints
    res = cu_hints.enum_clickables(scope="focused", timeout=6.0)
    rt = {"n": 0, "hit": 0, "offscreen": 0, "miss_hwnd_null": 0,
          "offsets": []}
    if res and res.get("elements"):
        import comtypes.client  # noqa
        comtypes.client.GetModule("UIAutomationCore.dll")
        import comtypes.gen.UIAutomationClient as uia_tlb
        uia = comtypes.client.CreateObject(
            "{ff48dba4-60ef-4201-aa87-54103eef594e}",
            interface=uia_tlb.IUIAutomation)
        by_name = {}
        for el in res["elements"]:
            b = el.get("bounds")
            if not b or not el.get("enabled", True):
                continue
            if el.get("offscreen"):
                rt["offscreen"] += 1
                continue
            cx = int(b[0] + b[2] / 2)
            cy = int(b[1] + b[3] / 2)
            rt["n"] += 1
            hit = None
            try:
                hit = uia.ElementFromPoint(
                    ctypes.wintypes.tagPOINT(cx, cy))
            except Exception:
                pass
            if hit is None:
                rt["miss_hwnd_null"] += 1
                continue
            try:
                hb = hit.CurrentBoundingRectangle
                inside = (hb.left <= cx < hb.right
                          and hb.top <= cy < hb.bottom)
                key = "hit" if inside else "outside"
                rt[key] = rt.get(key, 0) + 1
                rt["offsets"].append(
                    round(((hb.left + hb.right) / 2 - cx), 1))
            except Exception:
                rt["miss_hwnd_null"] += 1
            del hit
    report["roundtrip"] = rt
    report["focused_window"] = (res or {}).get("window")
    print(json.dumps(report, indent=1, default=str))
    if "--notepad" in sys.argv:
        np_proc.kill()


if __name__ == "__main__":
    main()
