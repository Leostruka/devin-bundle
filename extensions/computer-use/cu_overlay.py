#!/usr/bin/env python3
"""Ghost cursor + annotation overlay for computer-use (F3 S5/S6).

A per-pixel transparent, click-through, non-activating topmost window that
draws a *fake* cursor sprite and annotation primitives (box/label/arrow).
It never moves or reads the real cursor and never receives input - the
WS_EX_TRANSPARENT | NOACTIVATE pair guarantees zero input reach and zero
focus steal [F4 §4].

`--overlay-capture hidden` applies WDA_EXCLUDEFROMCAPTURE (Win10 2004+):
the overlay then also vanishes from the agent's own mss screenshots, so
--verify evidence frames never show the ghost. Default is visible.

CLI runs a pump for --hold ms; library use embeds GhostOverlay and drives
it through queue_command(). Windows-only.
"""
import argparse
import ctypes
import json
import math
import queue
import sys
import threading
import time
from ctypes import wintypes

# window flags
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020       # click-through: no input reach
WS_EX_NOACTIVATE = 0x08000000        # never steals focus
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080        # no taskbar entry
WS_POPUP = 0x80000000
LWA_COLORKEY = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Win10 2004+ only

KEY_COLOR = 0x00FF00FF               # magenta - the transparency key
CURSOR_COLOR = 0x00FFAA00            # blue-ish ghost sprite (BGR)
BOX_COLOR = 0x000000FF               # red (BGR)
LABEL_BG = 0x00000000


class OverlayError(Exception):
    pass


def fly_path(x0, y0, x1, y1, duration_ms=600, fps=90):
    """Bezier fly-to-target point list [(x,y,t_ms)] - arc like Clicky's
    buddy cursor. Midpoint control lifted perpendicular to the line."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy) or 1.0
    lift = min(80.0, norm * 0.18)
    cx, cy = mx - (dy / norm) * lift, my - (dx / norm) * lift
    steps = max(2, int(duration_ms / 1000 * fps))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        # quadratic bezier
        bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
        by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
        pts.append((int(bx), int(by), int(t * duration_ms)))
    return pts


def build_scene(cursor=None, boxes=None, arrows=None):
    """Plain drawing description - paint consumes this on the GUI thread."""
    return {"cursor": cursor, "boxes": boxes or [], "arrows": arrows or []}


class _Gdi32:
    """ctypes seam around window/GDI calls. Tests replace wholesale."""

    def __init__(self):
        self.u32 = ctypes.windll.user32
        self.g32 = ctypes.windll.gdi32
        self.k32 = ctypes.windll.kernel32
        self._wnd_proc = ctypes.WINFUNCTYPE(
            wintypes.LPARAM, wintypes.HWND, wintypes.UINT,
            wintypes.WPARAM, wintypes.LPARAM)


class GhostOverlay:
    """Full-screen overlay window + pump thread + command queue."""

    def __init__(self, capture="visible"):
        if sys.platform != "win32":
            raise OverlayError("platform:overlay_requires_windows")
        if capture not in ("visible", "hidden"):
            raise OverlayError(f"bad_capture:{capture}")
        self.g = _Gdi32()
        self.capture = capture
        self.hwnd = None
        self.scene = build_scene()
        self.queue = queue.Queue()
        self._ready = threading.Event()
        self._closed = threading.Event()

    # -- window lifecycle ------------------------------------------------
    def start(self):
        threading.Thread(target=self._pump, daemon=True,
                         name="cu-overlay").start()
        if not self._ready.wait(5.0):
            raise OverlayError("overlay_start_timeout")
        return self.hwnd

    def _pump(self):
        u, g = self.g.u32, self.g.g32
        sw = u.GetSystemMetrics(0)
        sh = u.GetSystemMetrics(1)
        self.hwnd = u.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
            | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
            "Static", "cu-ghost", WS_POPUP,
            0, 0, sw, sh, None, None, None, None)
        if not self.hwnd:
            self._ready.set()
            return
        u.SetLayeredWindowAttributes(self.hwnd, KEY_COLOR, 0, LWA_COLORKEY)
        if self.capture == "hidden":
            # fails on pre-2004 builds - degrade to visible, honestly
            ok = u.SetWindowDisplayAffinity(self.hwnd,
                                          WDA_EXCLUDEFROMCAPTURE)
            self.capture_applied = bool(ok)
        else:
            self.capture_applied = False
        u.ShowWindow(self.hwnd, 8)  # SW_SHOWNA - never activates
        self._ready.set()
        while not self._closed.is_set():
            try:
                cmd = self.queue.get(timeout=0.033)
            except queue.Empty:
                cmd = None
            if cmd is not None:
                self._apply(cmd)
            self._paint()

    def _apply(self, cmd):
        op = cmd.get("op")
        if op == "scene":
            self.scene = cmd["scene"]
        elif op == "close":
            self._closed.set()

    def _paint(self):
        u, g = self.g.u32, self.g.g32
        hdc = u.GetDC(self.hwnd)
        if not hdc:
            return
        try:
            g.SetBkMode(hdc, 1)  # TRANSPARENT
            brush = g.CreateSolidBrush(KEY_COLOR)
            r = wintypes.RECT(0, 0, 0, 0)
            u.GetClientRect(self.hwnd, ctypes.byref(r))
            u.FillRect(hdc, ctypes.byref(r), brush)
            g.DeleteObject(brush)
            self._draw_scene(hdc)
        finally:
            u.ReleaseDC(self.hwnd, hdc)

    def _draw_scene(self, hdc):
        g = self.g.g32
        scene = self.scene
        for box in scene["boxes"]:
            self._draw_box(hdc, box)
        for ar in scene["arrows"]:
            self._draw_arrow(hdc, ar)
        if scene["cursor"]:
            self._draw_cursor(hdc, *scene["cursor"])

    def _draw_cursor(self, hdc, x, y):
        g = self.g.g32
        pts = (wintypes.POINT * 3)(wintypes.POINT(x, y),
                                   wintypes.POINT(x, y + 16),
                                   wintypes.POINT(x + 11, y + 11))
        brush = g.CreateSolidBrush(CURSOR_COLOR)
        pen = g.CreatePen(0, 1, 0)  # PS_SOLID black outline
        old_b = g.SelectObject(hdc, brush)
        old_p = g.SelectObject(hdc, pen)
        g.Polygon(hdc, pts, 3)
        g.SelectObject(hdc, old_b)
        g.SelectObject(hdc, old_p)
        g.DeleteObject(brush)
        g.DeleteObject(pen)

    def _draw_box(self, hdc, box):
        g = self.g.g32
        l, t, w, h = box["rect"]
        pen = g.CreatePen(0, 2, BOX_COLOR)
        old = g.SelectObject(hdc, pen)
        g.Rectangle(hdc, l, t, l + w, t + h)
        g.SelectObject(hdc, old)
        g.DeleteObject(pen)
        label = box.get("label")
        if label:
            g.TextOutW(hdc, l + 4, t + 4, label, len(label))

    def _draw_arrow(self, hdc, ar):
        g = self.g.g32
        x0, y0, x1, y1 = ar["line"]
        pen = g.CreatePen(0, 2, BOX_COLOR)
        old = g.SelectObject(hdc, pen)
        g.MoveToEx(hdc, x0, y0, None)
        g.LineTo(hdc, x1, y1)
        g.SelectObject(hdc, old)
        g.DeleteObject(pen)

    # -- public API --------------------------------------------------------
    def show(self, cursor=None, boxes=None, arrows=None):
        self.queue.put({"op": "scene",
                        "scene": build_scene(cursor, boxes, arrows)})

    def fly_to(self, x, y, duration_ms=600, then_hold_ms=0,
               boxes=None, arrows=None):
        """Animate the ghost from its current (or screen-center) spot."""
        cur = self.scene.get("cursor")
        x0, y0 = cur if cur else (
            self.g.u32.GetSystemMetrics(0) // 2,
            self.g.u32.GetSystemMetrics(1) // 2)
        for px, py, _ in fly_path(x0, y0, x1=x, y1=y,
                                  duration_ms=duration_ms):
            self.show(cursor=(px, py), boxes=boxes, arrows=arrows)
            time.sleep(1 / 90)
        if then_hold_ms:
            time.sleep(then_hold_ms / 1000)

    def annotate(self, rect, label=None, arrow_from=None, ttl_ms=0):
        """Box + optional label over a target rect (e.g. UIA bounds)."""
        box = {"rect": list(rect), "label": label}
        arrows = []
        if arrow_from:
            l, t, w, h = rect
            arrows.append({"line": [arrow_from[0], arrow_from[1],
                                    l + w // 2, t + h // 2]})
        self.show(boxes=[box], arrows=arrows,
                  cursor=self.scene.get("cursor"))
        if ttl_ms:
            threading.Timer(ttl_ms / 1000,
                            lambda: self.show()).start()

    def close(self):
        self.queue.put({"op": "close"})
        self._closed.wait(2.0)


def main():
    ap = argparse.ArgumentParser(prog="cu_overlay.py")
    ap.add_argument("--fly", nargs=2, type=int, metavar=("X", "Y"),
                    help="fly ghost to screen coords")
    ap.add_argument("--annotate", nargs=4, type=int,
                    metavar=("L", "T", "W", "H"),
                    help="draw box over rect")
    ap.add_argument("--label", default=None)
    ap.add_argument("--overlay-capture", choices=["visible", "hidden"],
                    default="visible")
    ap.add_argument("--hold", type=int, default=1500,
                    help="ms to keep overlay up")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    try:
        ov = GhostOverlay(capture=args.overlay_capture)
        ov.start()
    except OverlayError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)
    try:
        if args.demo:
            ov.annotate((200, 200, 160, 60), label="target",
                        arrow_from=(100, 100))
            ov.fly_to(280, 230, duration_ms=700)
        if args.annotate:
            ov.annotate(tuple(args.annotate), label=args.label)
        if args.fly:
            ov.fly_to(*args.fly)
        time.sleep(args.hold / 1000)
    finally:
        ov.close()
    print(json.dumps({"ok": True, "capture": args.overlay_capture,
                      "capture_applied": ov.capture_applied}))


if __name__ == "__main__":
    main()
