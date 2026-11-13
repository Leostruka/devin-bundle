import sys
import time
import ctypes
import ctypes.wintypes as wt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pynput.keyboard import Controller, Key

kb = Controller()
u = ctypes.windll.user32
k = ctypes.windll.kernel32

# ensure focus on target
fg = u.GetForegroundWindow()
print("fg:", fg)

# WT select-all = ctrl+shift+a, copy = ctrl+shift+c
with kb.pressed(Key.ctrl_l, Key.shift):
    kb.tap("a")
time.sleep(0.5)
with kb.pressed(Key.ctrl_l, Key.shift):
    kb.tap("c")
time.sleep(0.5)

# read clipboard via win32 CF_UNICODETEXT
CF_UNICODETEXT = 13
if u.OpenClipboard(0):
    h = u.GetClipboardData(CF_UNICODETEXT)
    if h:
        size = k.GlobalSize(h)
        p = k.GlobalLock(h)
        data = ctypes.wstring_at(p, size // 2).rstrip("\x00")
        k.GlobalUnlock(h)
        print("clip len:", len(data))
        print("clip head:", data[:300].replace("\r", "\\r").replace("\n", "\\n"))
        print("clip tail:", data[-300:].replace("\r", "\\r").replace("\n", "\\n"))
    else:
        print("no CF_UNICODETEXT")
    u.CloseClipboard()
else:
    print("OpenClipboard failed")
