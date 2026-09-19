import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import comtypes.client

comtypes.client.GetModule("UIAutomationCore.dll")
uia_tlb = comtypes.gen.UIAutomationClient
uia = comtypes.client.CreateObject("{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=uia_tlb.IUIAutomation)

HWND = int(sys.argv[1])
root = uia.ElementFromHandle(HWND)


def walk(el, path, depth):
    if depth > 10:
        return
    try:
        cn = el.CurrentClassName
        ct = el.CurrentControlType
        name = el.CurrentName
    except Exception:
        return
    has_text = ""
    try:
        if el.GetCurrentPattern(uia_tlb.UIA_TextPatternId):
            has_text = " [TEXT]"
    except Exception:
        pass
    print(f"{path} [{cn}] ct={ct} {name[:40]!r}{has_text}")
    try:
        cond = uia.CreateTrueCondition()
        kids = el.FindAll(uia_tlb.TreeScope_Children, cond)
        for i in range(kids.Length):
            walk(kids.GetElement(i), f"{path}.{i}", depth + 1)
    except Exception as e:
        print(f"{path} children err: {e}")


walk(root, "r", 0)
print("done")
