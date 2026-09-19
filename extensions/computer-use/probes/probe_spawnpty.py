import ctypes
import ctypes.wintypes as wt
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
k = ctypes.windll.kernel32

HANDLE = wt.HANDLE
INVALID = HANDLE(-1).value


class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", wt.DWORD), ("lpSecurityDescriptor", wt.LPVOID), ("bInheritHandle", wt.BOOL)]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
                ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD), ("dwXCountChars", wt.DWORD),
                ("dwYCountChars", wt.DWORD), ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD), ("lpReserved2", wt.LPVOID),
                ("hStdInput", HANDLE), ("hStdOutput", HANDLE), ("hStdError", HANDLE)]


class STARTUPINFOEX(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFO), ("lpAttributeList", wt.LPVOID)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", HANDLE), ("hThread", HANDLE), ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016
EXTENDED_STARTUPINFO_PRESENT = 0x00080000

# named pipes estilo winpty: server end vai pro PTY, client end fica conosco
PIPE_ACCESS_DUPLEX = 0x3
FILE_FLAG_FIRST_PIPE_INSTANCE = 0x80000
PIPE_TYPE_BYTE = 0
PIPE_READMODE_BYTE = 0
PIPE_WAIT = 0
import os
tag = os.getpid()

def make_pair(name):
    srv = k.CreateNamedPipeW(
        f"\\\\.\\pipe\\{name}-{tag}",
        PIPE_ACCESS_DUPLEX | FILE_FLAG_FIRST_PIPE_INSTANCE,
        PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
        1, 131072, 131072, 0, None)
    if srv == INVALID or srv is None:
        print("CreateNamedPipe failed:", name, k.GetLastError())
        sys.exit(1)
    cli = k.CreateFileW(f"\\\\.\\pipe\\{name}-{tag}", 0x80000000 | 0x40000000,
                        0, None, 3, 0, None)
    if cli == INVALID or cli is None:
        print("CreateFile client failed:", name, k.GetLastError())
        sys.exit(1)
    return srv, cli

hInR, hInW = make_pair("cupty-in")    # pty lê hInR; nós escrevemos hInW
hOutW, hOutR = make_pair("cupty-out") # pty escreve hOutW; nós lemos hOutR

hPC = HANDLE()
size = COORD(120, 30)
hr = k.CreatePseudoConsole(size, hInR, hOutW, 0, ctypes.byref(hPC))
if hr != 0:
    print("CreatePseudoConsole failed:", hr)
    sys.exit(1)
print("hPC:", hPC.value, "err:", k.GetLastError())
import os, subprocess
time.sleep(0.5)
me = os.getpid()
out = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     f"Get-CimInstance Win32_Process -Filter \"ParentProcessId={me}\" | Select-Object ProcessId,Name | Format-Table -HideTableHeaders | Out-String"],
    capture_output=True, text=True)
print("children of python:", out.stdout.strip())

# NOTA: mantemos os ends do lado do pty abertos nesta build —
# fechar hOutW silenciava o relay de output (observado nesta máquina)
_KEEP_PTY_ENDS = True
if not _KEEP_PTY_ENDS:
    k.CloseHandle(hInR)
    k.CloseHandle(hOutW)

# attribute list — argtypes explicitos para evitar truncamento 32-bit
k.InitializeProcThreadAttributeList.argtypes = [wt.LPVOID, wt.DWORD, wt.DWORD, ctypes.POINTER(ctypes.c_size_t)]
k.UpdateProcThreadAttribute.argtypes = [wt.LPVOID, wt.DWORD, ctypes.c_size_t, wt.LPVOID, ctypes.c_size_t, wt.LPVOID, wt.LPVOID]
k.DeleteProcThreadAttributeList.argtypes = [wt.LPVOID]

attr_size = ctypes.c_size_t(0)
k.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(attr_size))
buf = ctypes.create_string_buffer(attr_size.value)
plist = ctypes.cast(buf, wt.LPVOID)
if not k.InitializeProcThreadAttributeList(plist, 1, 0, ctypes.byref(attr_size)):
    print("InitAttrList failed:", k.GetLastError())
    sys.exit(1)

if not k.UpdateProcThreadAttribute(
    plist, 0, PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
    ctypes.cast(hPC, wt.LPVOID), ctypes.c_size_t(ctypes.sizeof(hPC)), None, None
):
    print("UpdateAttr failed:", k.GetLastError())
    sys.exit(1)

si = STARTUPINFOEX()
si.StartupInfo.cb = ctypes.sizeof(STARTUPINFOEX)
si.lpAttributeList = ctypes.cast(buf, wt.LPVOID)
print("attrlist@:", hex(ctypes.addressof(buf)), "si.lpAttributeList:", hex(si.lpAttributeList or 0))

pi = PROCESS_INFORMATION()
k.CreateProcessW.restype = wt.BOOL
ok = k.CreateProcessW(None, "powershell.exe -NoExit -Command $null", None, None, False,
                      EXTENDED_STARTUPINFO_PRESENT, None, None,
                      ctypes.cast(ctypes.byref(si), wt.LPVOID), ctypes.byref(pi))
if not ok:
    print("CreateProcess failed:", k.GetLastError())
    sys.exit(1)
print("spawned pid:", pi.dwProcessId)
k.DeleteProcThreadAttributeList(plist)


def read_avail(deadline_s=2.0):
    out = b""
    end = time.time() + deadline_s
    while time.time() < end:
        avail = wt.DWORD(0)
        if not k.PeekNamedPipe(hOutR, None, 0, None, ctypes.byref(avail), None):
            break
        if avail.value == 0:
            time.sleep(0.05)
            continue
        chunk = ctypes.create_string_buffer(avail.value)
        n = wt.DWORD(0)
        if not k.ReadFile(hOutR, chunk, avail.value, ctypes.byref(n), None):
            break
        out += chunk.raw[: n.value]
    return out


time.sleep(0.8)
ec = wt.DWORD(0)
k.GetExitCodeProcess(pi.hProcess, ctypes.byref(ec))
print("exit code:", ec.value, "(259=still running)")

# diagnostico: child tem console? lista processos do console dele
n = wt.DWORD(0)
cnt = k.GetConsoleProcessList(ctypes.byref(n), 1)
print("console process list count:", cnt)

# tenta attach no console do child e ler CONOUT$
k.FreeConsole()
if k.AttachConsole(pi.dwProcessId):
    h2 = k.CreateFileW("CONOUT$", 0x80000000 | 0x40000000, 3, None, 3, 0, None)
    print("child CONOUT$:", h2 != -1 and h2 is not None)

    class _CSBI(ctypes.Structure):
        _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                    ("wAttributes", wt.WORD),
                    ("srWindow", ctypes.c_short * 4),
                    ("dwMaximumWindowSize", COORD)]
    class _CI(ctypes.Structure):
        _fields_ = [("Char", ctypes.c_wchar * 1), ("Attributes", wt.WORD)]
    cs = _CSBI()
    if k.GetConsoleScreenBufferInfo(h2, ctypes.byref(cs)):
        w2, hgt2 = cs.dwSize.X, cs.dwSize.Y
        print("child buf:", w2, "x", hgt2, "cursor:", cs.dwCursorPosition.X, cs.dwCursorPosition.Y)
        nb = w2 * min(hgt2, 40)
        bb = (_CI * nb)()
        rc = COORD(0, 0)
        class SR(ctypes.Structure):
            _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short), ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]
        rect2 = SR(0, 0, w2 - 1, min(hgt2, 40) - 1)
        if k.ReadConsoleOutputW(h2, bb, COORD(w2, min(hgt2, 40)), rc, ctypes.byref(rect2)):
            for y in range(rect2.Top, rect2.Bottom + 1):
                ln = "".join(bb[y * w2 + x].Char[0] for x in range(w2)).rstrip()
                if ln:
                    print(" |", ln[:100])
    k.FreeConsole()
else:
    print("attach child failed:", k.GetLastError())

w = wt.DWORD(0)
okw = k.WriteFile(hInW, b"echo cu-pty-ok\r\n", 17, ctypes.byref(w), None)
print("write in:", okw, "n:", w.value, "err:", k.GetLastError())
time.sleep(1.0)

avail = wt.DWORD(0)
okpk = k.PeekNamedPipe(hOutR, None, 0, None, ctypes.byref(avail), None)
print("peek ok:", okpk, "avail:", avail.value, "err:", k.GetLastError())
banner = read_avail(4.0)
print("=== banner+resp ===")
print(repr(banner[:1500]))
print("marker found:", b"cu-pty-ok" in banner)
resp = banner  # reuse

# exit cleanly
k.WriteFile(hInW, b"exit\r\n", 6, ctypes.byref(w), None)
k.WaitForSingleObject(pi.hProcess, 3000)
tail = read_avail(0.5)
k.ClosePseudoConsole(hPC)
k.CloseHandle(hInW)
k.CloseHandle(hOutR)
k.CloseHandle(pi.hProcess)
k.CloseHandle(pi.hThread)
print("done, tail:", repr(tail[:200]))
