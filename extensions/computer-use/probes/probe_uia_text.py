import sys
import comtypes
import comtypes.client

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
comtypes.CoInitialize()
uia_tlb = comtypes.client.GetModule("UIAutomationCore.dll")

uia = comtypes.client.CreateObject(
    "{ff48dba4-60ef-4201-aa87-54103eef594e}",
    interface=uia_tlb.IUIAutomation)

hwnd = int(sys.argv[1])
root = uia.ElementFromHandle(hwnd)
UIA_TextPatternId = 10014


def walk(el, depth, path):
    if depth > 14:
        return
    try:
        cls = el.CurrentClassName or ""
        if cls == "TermControl":
            tp = el.GetCurrentPattern(UIA_TextPatternId)
            tp = tp.QueryInterface(uia_tlb.IUIAutomationTextPattern)
            doc = tp.DocumentRange
            txt = doc.GetText(-1)
            print(f"=== TermControl @ {path} len={len(txt)} ===")
            print(txt[:3000])
            print("=== end ===")
    except Exception as e:
        print("term err:", e)
    try:
        kids = el.FindAll(4, uia.CreateTrueCondition())
        for i in range(kids.Length):
            walk(kids.GetElement(i), depth + 1, f"{path}.{i}")
    except Exception:
        pass


walk(root, 0, "r")
print("done")
