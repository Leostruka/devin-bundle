import ctypes
import sys
from ctypes import wintypes

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
kernel32 = ctypes.windll.kernel32


class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]


class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                ("wAttributes", wintypes.WORD), ("srWindow", SMALL_RECT),
                ("dwMaximumWindowSize", COORD)]


class CHAR_INFO(ctypes.Structure):
    _fields_ = [("Char", ctypes.c_wchar * 1), ("Attributes", wintypes.WORD)]


pid = int(sys.argv[1])
kernel32.FreeConsole()
if not kernel32.AttachConsole(pid):
    print("AttachConsole failed:", ctypes.get_last_error() if hasattr(ctypes, "get_last_error") else kernel32.GetLastError())
    sys.exit(1)

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
OPEN_EXISTING = 3
h = kernel32.CreateFileW("CONOUT$", GENERIC_READ | GENERIC_WRITE,
                         FILE_SHARE_READ | FILE_SHARE_WRITE, None,
                         OPEN_EXISTING, 0, None)
if h in (0, -1) or h == wintypes.HANDLE(-1).value:
    print("CreateFile CONOUT$ failed:", kernel32.GetLastError())
    sys.exit(1)
info = CONSOLE_SCREEN_BUFFER_INFO()
if not kernel32.GetConsoleScreenBufferInfo(h, ctypes.byref(info)):
    print("GetConsoleScreenBufferInfo failed:", kernel32.GetLastError())
    sys.exit(1)
w, hgt = info.dwSize.X, info.dwSize.Y
print("buffer:", w, "x", hgt, "cursor:", info.dwCursorPosition.X, info.dwCursorPosition.Y)

n = w * hgt
buf = (CHAR_INFO * n)()
coord = COORD(0, 0)
rect = SMALL_RECT(0, 0, w - 1, hgt - 1)
if not kernel32.ReadConsoleOutputW(h, buf, COORD(w, hgt), coord, ctypes.byref(rect)):
    print("ReadConsoleOutput failed:", kernel32.GetLastError())
    sys.exit(1)
lines = []
for y in range(rect.Top, rect.Bottom + 1):
    line = "".join(buf[y * w + x].Char[0] for x in range(w)).rstrip()
    lines.append(line)
print(f"=== buffer {w}x{hgt} window={info.srWindow.Top}-{info.srWindow.Bottom} ===")
nonempty = [f"{i}: {l}" for i, l in enumerate(lines) if l.strip()]
print("\n".join(nonempty[-40:]))
kernel32.FreeConsole()
print("=== done ===")
