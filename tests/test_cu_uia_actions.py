"""Etapa 3 gates: uia_perform re-locates the live element and runs the
right pattern — typed rejections for stale / no_pattern / readonly, and
FindAllBuildCache used for the enumeration."""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load

cu_hints = load("cu_hints")


class FakeRect:
    def __init__(self, l, t, r, b):
        self.left, self.top, self.right, self.bottom = l, t, r, b


class FakePattern:
    def __init__(self, readonly=False):
        self.calls = []
        self.CurrentIsReadOnly = readonly

    def Invoke(self):
        self.calls.append("Invoke")

    def SetValue(self, text):
        self.calls.append(("SetValue", text))


class FakeElement:
    def __init__(self, ct, name, rect, enabled=True, hwnd=100):
        self.CachedControlType = ct
        self.CachedName = name
        self.CachedBoundingRectangle = rect
        self.CachedIsEnabled = enabled
        self.CachedNativeWindowHandle = hwnd
        self.patterns = {}

    def GetCurrentPattern(self, pid):
        return self.patterns.get(pid)


class FakeArray:
    def __init__(self, els):
        self.Length = len(els)
        self._els = els

    def GetElement(self, i):
        return self._els[i]


class FakeTarget:
    def __init__(self, els):
        self.els = els
        self.used_cache = False

    def FindAllBuildCache(self, scope, cond, req):
        self.used_cache = True
        return FakeArray(self.els)

    def FindAll(self, scope, cond):
        return FakeArray(self.els)


class FakeCore:
    def __init__(self, target):
        self.target = target
        self.cache_requests = []

    def CreatePropertyCondition(self, pid, val):
        return ("prop", pid, val)

    def CreateOrCondition(self, a, b):
        return ("or", a, b)

    def CreateAndCondition(self, a, b):
        return ("and", a, b)

    def CreateCacheRequest(self):
        r = types.SimpleNamespace(props=[], AddProperty=None)
        r.AddProperty = r.props.append
        self.cache_requests.append(r)
        return r

    def ElementFromHandle(self, hwnd):
        return self.target


@pytest.fixture
def fake_uia(monkeypatch):
    state = {"core": None}
    comtypes = types.ModuleType("comtypes")
    comtypes.CoInitialize = lambda: None
    comtypes.CoUninitialize = lambda: None
    sub = types.ModuleType("uiautomation.uiautomation")

    class Client:
        @staticmethod
        def instance():
            return types.SimpleNamespace(IUIAutomation=state["core"])

    sub._AutomationClient = Client
    pkg = types.ModuleType("uiautomation")
    pkg.uiautomation = sub
    monkeypatch.setitem(sys.modules, "comtypes", comtypes)
    monkeypatch.setitem(sys.modules, "uiautomation", pkg)
    monkeypatch.setitem(sys.modules, "uiautomation.uiautomation", sub)
    monkeypatch.setattr(cu_hints.os, "name", "nt")
    monkeypatch.delenv("CU_NO_UIA", raising=False)
    return state


def _entry(**kw):
    e = {"x": 150, "y": 60, "name": "Salvar", "type": "Button",
         "bounds": [140, 50, 20, 20], "hwnd": 100, "enabled": True}
    e.update(kw)
    return e


def _button(patterns=None, name="Salvar", rect=None, hwnd=100):
    el = FakeElement(50000, name, rect or FakeRect(140, 50, 160, 70),
                     hwnd=hwnd)
    el.patterns = patterns or {}
    return el


def test_invoke_relocates_and_invokes(fake_uia):
    inv = FakePattern()
    target = FakeTarget([_button({10000: inv})])
    fake_uia["core"] = FakeCore(target)
    res, reason = cu_hints.uia_perform(_entry(), "invoke")
    assert reason is None and res["pattern"] == "Invoke"
    assert inv.calls == ["Invoke"]
    assert (res["x"], res["y"]) == (150, 60)


def test_enum_uses_build_cache(fake_uia):
    target = FakeTarget([_button({10000: FakePattern()})])
    core = FakeCore(target)
    fake_uia["core"] = core
    cu_hints.uia_perform(_entry(), "locate")
    assert target.used_cache is True
    assert core.cache_requests and 30001 in core.cache_requests[0].props


def test_missing_element_is_stale(fake_uia):
    fake_uia["core"] = FakeCore(FakeTarget([]))
    res, reason = cu_hints.uia_perform(_entry(), "invoke")
    assert res is None and reason == "stale"


def test_no_pattern_typed_reason(fake_uia):
    fake_uia["core"] = FakeCore(FakeTarget([_button()]))
    res, reason = cu_hints.uia_perform(_entry(), "invoke")
    assert reason == "no_pattern" and res["x"] == 150


def test_set_value_and_readonly(fake_uia):
    ok_el = _button({10002: FakePattern()})
    fake_uia["core"] = FakeCore(FakeTarget([ok_el]))
    res, reason = cu_hints.uia_perform(_entry(), "set_value", "texto")
    assert reason is None and res["pattern"] == "Value"
    assert ok_el.patterns[10002].calls == [("SetValue", "texto")]

    ro_el = _button({10002: FakePattern(readonly=True)})
    fake_uia["core"] = FakeCore(FakeTarget([ro_el]))
    res, reason = cu_hints.uia_perform(_entry(), "set_value", "x")
    assert reason == "readonly"
    assert ro_el.patterns[10002].calls == []


def test_nearest_same_type_wins(fake_uia):
    far = _button({10000: FakePattern()}, name="longe",
                  rect=FakeRect(500, 500, 520, 520))
    near = _button({10000: FakePattern()}, name="perto")
    fake_uia["core"] = FakeCore(FakeTarget([far, near]))
    res, reason = cu_hints.uia_perform(_entry(), "invoke")
    assert reason is None
    assert near.patterns[10000].calls == ["Invoke"]
    assert far.patterns[10000].calls == []


def test_no_hwnd_rejected(fake_uia):
    fake_uia["core"] = FakeCore(FakeTarget([_button()]))
    res, reason = cu_hints.uia_perform(_entry(hwnd=None), "invoke")
    assert res is None and reason == "no_hwnd"


def test_nocache_forces_per_element_roundtrips(fake_uia, monkeypatch):
    """Ticket 17: CU_HINT_NOCACHE bypasses FindAllBuildCache -> every
    element pays live property reads. Cache path pays zero."""
    reads = {"n": 0}

    class Counting(FakeElement):
        @property
        def CurrentBoundingRectangle(self):
            reads["n"] += 1
            return self.CachedBoundingRectangle

        @property
        def CurrentControlType(self):
            reads["n"] += 1
            return self.CachedControlType

        @property
        def CurrentName(self):
            reads["n"] += 1
            return self.CachedName

        @property
        def CurrentIsEnabled(self):
            reads["n"] += 1
            return self.CachedIsEnabled

        @property
        def CurrentNativeWindowHandle(self):
            reads["n"] += 1
            return self.CachedNativeWindowHandle

    els = [Counting(50000, f"b{i}", FakeRect(10 * i, 10 * i, 10 * i + 30,
                                             10 * i + 20), hwnd=100 + i)
           for i in range(4)]
    target = FakeTarget(els)
    fake_uia["core"] = FakeCore(target)

    monkeypatch.setenv("CU_HINT_NOCACHE", "1")
    out = cu_hints._enum_elements(fake_uia["core"], target)
    assert len(out) == 4
    assert reads["n"] == 4 * 5  # 5 live props per element, zero cache
    assert target.used_cache is False

    reads["n"] = 0
    monkeypatch.delenv("CU_HINT_NOCACHE")
    out = cu_hints._enum_elements(fake_uia["core"], target)
    assert len(out) == 4
    assert reads["n"] == 0      # cached path: no live property reads
    assert target.used_cache is True
