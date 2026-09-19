import sys
import time
import ctypes

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import comtypes.client

comtypes.client.GetModule("UIAutomationCore.dll")
uia_tlb = comtypes.gen.UIAutomationClient
uia = comtypes.client.CreateObject("{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=uia_tlb.IUIAutomation)

HWND = 460176
root = uia.ElementFromHandle(HWND)
cond = uia.CreatePropertyCondition(uia_tlb.UIA_ClassNamePropertyId, "TermControl")
terms = root.FindAll(uia_tlb.TreeScope_Subtree, cond)
print("terms:", terms.Length)

PATTERNS = {
    "Invoke": uia_tlb.UIA_InvokePatternId,
    "Scroll": uia_tlb.UIA_ScrollPatternId,
    "ScrollItem": uia_tlb.UIA_ScrollItemPatternId,
    "Value": uia_tlb.UIA_ValuePatternId,
    "Selection": uia_tlb.UIA_SelectionPatternId,
    "SelectionItem": uia_tlb.UIA_SelectionItemPatternId,
    "Text": uia_tlb.UIA_TextPatternId,
    "TextEdit": getattr(uia_tlb, "UIA_TextEditPatternId", 10032),
    "Transform": uia_tlb.UIA_TransformPatternId,
    "Dock": uia_tlb.UIA_DockPatternId,
}

for i in range(terms.Length):
    el = terms.GetElement(i)
    name = el.CurrentName
    print(f"--- TermControl {i} '{name}'")
    for pname, pid in PATTERNS.items():
        try:
            ok = el.GetCurrentPattern(pid)
            print(f"  {pname}: {'YES' if ok else 'no'}")
        except Exception as e:
            print(f"  {pname}: err {e}")

# text selection state
el = terms.GetElement(0)
tp = el.GetCurrentPattern(uia_tlb.UIA_TextPatternId).QueryInterface(uia_tlb.IUIAutomationTextPattern)
try:
    sel = tp.GetSelection()
    print("selection ranges:", sel.Length)
    for i in range(sel.Length):
        r = sel.GetElement(i)
        t = r.GetText(80)
        print(f"  sel[{i}]: {t!r}")
except Exception as e:
    print("GetSelection err:", e)
