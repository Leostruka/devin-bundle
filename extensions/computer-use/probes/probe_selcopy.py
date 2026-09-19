import sys
import time
import ctypes

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import comtypes.client
from pynput.keyboard import Controller, Key

comtypes.client.GetModule("UIAutomationCore.dll")
uia_tlb = comtypes.gen.UIAutomationClient
uia = comtypes.client.CreateObject("{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=uia_tlb.IUIAutomation)

HWND = 460176
u = ctypes.windll.user32
k = ctypes.windll.kernel32

root = uia.ElementFromHandle(HWND)
cond = uia.CreatePropertyCondition(uia_tlb.UIA_ClassNamePropertyId, "TermControl")
terms = root.FindAll(uia_tlb.TreeScope_Subtree, cond)
el = terms.GetElement(0)
tp = el.GetCurrentPattern(uia_tlb.UIA_TextPatternId).QueryInterface(uia_tlb.IUIAutomationTextPattern)
doc = tp.DocumentRange

# select whole document via UIA (no focus needed)
try:
    doc.Select()
    print("Select() ok")
    time.sleep(0.4)
    sel = tp.GetSelection()
    r = sel.GetElement(0)
    t = r.GetText(-1)
    print("selected len:", len(t))
except Exception as e:
    print("Select err:", e)

# focus window then copy
fg = u.GetForegroundWindow()
tid_fg = u.GetWindowThreadProcessId(fg, None)
tid_me = k.GetCurrentThreadId()
u.AttachThreadInput(tid_me, tid_fg, True)
u.SetForegroundWindow(HWND)
u.BringWindowToTop(HWND)
u.AttachThreadInput(tid_me, tid_fg, False)
time.sleep(0.4)
print("fg:", u.GetForegroundWindow(), "target:", HWND)

kb = Controller()
with kb.pressed(Key.ctrl_l, Key.shift):
    kb.tap("c")
time.sleep(0.5)

# also try plain ctrl+c in case binding is default
if True:
    # read clipboard first attempt
    CF = 13
    def read_clip():
        if u.OpenClipboard(0):
            h = u.GetClipboardData(CF)
            data = ""
            if h:
                size = k.GlobalSize(h)
                p = k.GlobalLock(h)
                data = ctypes.wstring_at(p, size // 2).rstrip("\x00")
                k.GlobalUnlock(h)
            u.CloseClipboard()
            return data
        return None
    d = read_clip()
    print("clip after ctrl+shift+c:", 0 if d is None else len(d))
    if not d:
        with kb.pressed(Key.ctrl_l):
            kb.tap("c")
        time.sleep(0.5)
        d = read_clip()
        print("clip after ctrl+c:", 0 if d is None else len(d))
    if d:
        print("head:", d[:200].replace("\r", "\\r").replace("\n", "\\n"))
        print("tail:", d[-200:].replace("\r", "\\r").replace("\n", "\\n"))
