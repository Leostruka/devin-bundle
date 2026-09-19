import ctypes
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
u = ctypes.windll.user32
k = ctypes.windll.kernel32

HWND = 460176

# focus: AttachThreadInput trick
fg = u.GetForegroundWindow()
tid_fg = u.GetWindowThreadProcessId(fg, None)
tid_me = k.GetCurrentThreadId()
u.AttachThreadInput(tid_me, tid_fg, True)
u.SetForegroundWindow(HWND)
u.BringWindowToTop(HWND)
u.AttachThreadInput(tid_me, tid_fg, False)
time.sleep(0.4)
print("fg now:", u.GetForegroundWindow(), "target:", HWND)

from pynput.keyboard import Controller, Key

kb = Controller()
kb.type("echo cu-type-ok")
time.sleep(0.3)
print("typed")
