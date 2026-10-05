#!/usr/bin/env python3
"""Foreign target window for p1_winevents probe.
Creates a plain win32 window titled sys.argv[1], pumps messages for
sys.argv[2] seconds, exits. Stdlib only."""
import ctypes
import ctypes.wintypes as wt
import sys
import time

u = ctypes.windll.user32
k = ctypes.windll.kernel32

title = sys.argv[1]
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 60
qpc_out = "--qpc" in sys.argv
draw_text = "--drawtext" in sys.argv
topmost = "--topmost" in sys.argv

WNDPROC = ctypes.WINFUNCTYPE(wt.LPARAM, wt.HWND, wt.UINT,
                             wt.WPARAM, wt.LPARAM)
u.DefWindowProcW.restype = wt.LPARAM
u.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]

TEXT_LINES = ["File Edit View Help", "The quick brown fox 12345",
              "cu-perception OCR probe", "Apply  Cancel  OK"]


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [("hdc", wt.HDC), ("fErase", wt.BOOL),
                ("rcPaint", wt.RECT), ("fRestore", wt.BOOL),
                ("fIncUpdate", wt.BOOL), ("rgbReserved", ctypes.c_byte * 32)]


def _wndproc(h, m, w, l):
    if m == 0x000F and draw_text:  # WM_PAINT
        ps = PAINTSTRUCT()
        hdc = u.BeginPaint(h, ctypes.byref(ps))
        ctypes.windll.gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
        y = 12
        for line in TEXT_LINES:
            r = wt.RECT(12, y, 600, y + 24)
            u.DrawTextW(hdc, line, -1, ctypes.byref(r), 0)
            y += 28
        u.EndPaint(h, ctypes.byref(ps))
        return 0
    return u.DefWindowProcW(h, m, w, l)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("style", wt.UINT),
                ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE),
                ("hIcon", wt.HICON), ("hCursor", wt.HCURSOR),
                ("hbrBackground", wt.HBRUSH), ("lpszMenuName", wt.LPCWSTR),
                ("lpszClassName", wt.LPCWSTR), ("hIconSm", wt.HICON)]


_cb = WNDPROC(_wndproc)
k.GetModuleHandleW.restype = wt.HMODULE
wc = WNDCLASSEXW()
wc.cbSize = ctypes.sizeof(wc)
wc.lpfnWndProc = _cb
wc.lpszClassName = "cu_p1_target"
wc.hInstance = k.GetModuleHandleW(None)
wc.hbrBackground = 5  # COLOR_WINDOW
u.RegisterClassExW(ctypes.byref(wc))
u.CreateWindowExW.restype = wt.HWND
if qpc_out:
    c, f = ctypes.c_int64(), ctypes.c_int64()
    k.QueryPerformanceFrequency(ctypes.byref(f))
    k.QueryPerformanceCounter(ctypes.byref(c))
    print(c.value, f.value, flush=True)
hwnd = u.CreateWindowExW(0x8 if topmost else 0, "cu_p1_target", title,
                         0x00CF0000, 400, 300, 320, 200, None, None,
                         wt.HINSTANCE(wc.hInstance), None)
u.ShowWindow(hwnd, 5)  # SW_SHOW
u.UpdateWindow(hwnd)
if topmost:
    u.SetWindowPos(hwnd, wt.HWND(-1), 0, 0, 0, 0, 0x0001 | 0x0002)

deadline = time.time() + secs
msg = wt.MSG()
while time.time() < deadline:
    while u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
        u.TranslateMessage(ctypes.byref(msg))
        u.DispatchMessageW(ctypes.byref(msg))
    time.sleep(0.01)
