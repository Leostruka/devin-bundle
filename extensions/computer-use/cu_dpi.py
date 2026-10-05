"""Shared DPI awareness + physical window geometry (P3 integration).

Every entry point that reads screen coordinates must set awareness
before the first read — a fresh python process starts DPI-unaware and
gets virtualized (wrong) coordinates on scaled displays. Per-monitor v2
(-4) is the correct context; shcore v2 / user32 are fallbacks for older
systems.

For window geometry, GetWindowRect includes invisible resize borders
(~5px on many windows) — DWMWA_EXTENDED_FRAME_BOUNDS gives the visible
frame and matches UIA/pixel space.
"""
import ctypes
import sys
import ctypes.wintypes as wt

_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
_DWMWA_EXTENDED_FRAME_BOUNDS = 9


def set_dpi_awareness():
    """Per-monitor v2 -> shcore v2 -> user32 fallback chain. Returns
    which mechanism took: 'pmv2' | 'shcore' | 'user32' | None."""
    if sys.platform != "win32":
        return None
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(
                ctypes.c_void_p(
                    _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)):
            return "pmv2"
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return "shcore"
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return "user32"
    except Exception:
        return None


def physical_window_bounds(hwnd):
    """Visible frame rect (l, t, r, b) via DWM extended bounds; falls
    back to GetWindowRect when DWM is unavailable."""
    if sys.platform != "win32":
        raise OSError("windows only")
    r = wt.RECT()
    try:
        hr = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wt.HWND(int(hwnd)),
            wt.DWORD(_DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(r), ctypes.sizeof(r))
        if hr == 0:
            return r.left, r.top, r.right, r.bottom
    except Exception:
        pass
    if not ctypes.windll.user32.GetWindowRect(int(hwnd), ctypes.byref(r)):
        raise OSError(f"no_rect:{hwnd}")
    return r.left, r.top, r.right, r.bottom
