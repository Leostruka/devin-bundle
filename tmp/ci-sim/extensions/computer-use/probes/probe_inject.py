import sys
import time
import ctypes
import ctypes.wintypes as wt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
k = ctypes.windll.kernel32
u = ctypes.windll.user32

PID = 33720

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
OPEN_EXISTING = 3


class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wt.BOOL),
        ("wRepeatCount", wt.WORD),
        ("wVirtualKeyCode", wt.WORD),
        ("wVirtualScanCode", wt.WORD),
        ("UnicodeChar", wt.WCHAR),
        ("dwControlKeyState", wt.DWORD),
    ]


class INPUT_RECORD_EVENT(ctypes.Union):
    _fields_ = [("KeyEvent", KEY_EVENT_RECORD), ("Pad", ctypes.c_byte * 16)]


class INPUT_RECORD(ctypes.Structure):
    _fields_ = [("EventType", wt.WORD), ("Event", INPUT_RECORD_EVENT)]


k.FreeConsole()
if not k.AttachConsole(PID):
    print("attach failed:", ctypes.GetLastError())
    sys.exit(1)
print("attached")

h = k.CreateFileW("CONIN$", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None)
if h == -1 or h is None:
    print("CONIN$ failed:", ctypes.GetLastError())
    k.FreeConsole()
    sys.exit(1)
print("CONIN$ open")

def send(text):
    # VK=0 + UnicodeChar = en guvenli metin enjeksiyonu
    for ch in text:
        recs = (INPUT_RECORD * 2)()
        for i, down in enumerate((True, False)):
            r = recs[i]
            r.EventType = 1
            ke = r.Event.KeyEvent
            ke.bKeyDown = down
            ke.wRepeatCount = 1
            ke.wVirtualKeyCode = 0x0D if ch == "\r" else 0
            ke.wVirtualScanCode = 0
            ke.UnicodeChar = ch
            ke.dwControlKeyState = 0
        written = wt.DWORD(0)
        k.WriteConsoleInputW(h, recs, 2, ctypes.byref(written))
        time.sleep(0.02)
    print("sent:", repr(text))

send(" echo cu-inject-ok")
time.sleep(0.3)
send("\r")
time.sleep(0.8)
k.CloseHandle(h)
k.FreeConsole()
print("done")
