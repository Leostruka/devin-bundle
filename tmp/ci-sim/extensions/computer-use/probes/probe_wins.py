import ctypes
import sys
from ctypes import wintypes

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
u = ctypes.windll.user32
k = ctypes.windll.kernel32

rows = []


def cb(hwnd, _):
    if not u.IsWindowVisible(hwnd):
        return True
    n = u.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    u.GetWindowTextW(hwnd, buf, n + 1)
    pid = ctypes.c_ulong(0)
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    cn = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(hwnd, cn, 256)
    rows.append((hwnd, pid.value, cn.value, buf.value))
    return True


WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
u.EnumWindows(WNDENUMPROC(cb), 0)
for h, p, c, t in rows:
    if "CASCADIA" in c or "Console" in c or "Terminal" in c or "PseudoConsole" in c:
        print(f"hwnd={h} pid={p} class={c} title={t!r}")
print("---- all titled windows:")
for h, p, c, t in rows:
    if t:
        print(f"hwnd={h} pid={p} class={c[:40]} title={t[:60]!r}")
