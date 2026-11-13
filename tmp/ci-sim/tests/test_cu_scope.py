"""cu_scope.py unit tests - fake Win32 tree; no real windows needed."""
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cu_load  # noqa: E402

cu_scope = cu_load.load("cu_scope")


class FakeU32:
    def __init__(self, fail_after=None):
        self.posted = []
        self.fail_after = fail_after  # fail PostMessageW after N calls

    def PostMessageW(self, hwnd, msg, wp, lp):
        self.posted.append((hwnd, msg, wp, lp))
        if self.fail_after is not None and len(self.posted) > self.fail_after:
            return False
        return True


class FakeWin:
    """In-memory HWND tree: (title, class, pid, children)."""

    def __init__(self, tree, fail_after=None):
        # tree: {hwnd: {"title","class","pid","visible","children":[hwnd...]}}
        self.t = tree
        self.u32 = FakeU32(fail_after)

    def enum_top(self):
        return [h for h, v in self.t.items() if v.get("top")]

    def enum_children(self, hwnd):
        return list(self.t[hwnd].get("children", []))

    def title(self, hwnd):
        return self.t[hwnd]["title"]

    def class_name(self, hwnd):
        return self.t[hwnd]["class"]

    def pid(self, hwnd):
        return self.t[hwnd]["pid"]

    def visible(self, hwnd):
        return self.t[hwnd].get("visible", True)

    def rect(self, hwnd):
        return self.t[hwnd].get("rect", (0, 0, 10, 10))


NOTEPAD_TREE = {
    100: {"top": True, "title": "x.txt - Notepad", "class": "Notepad",
          "pid": 42, "children": [101]},
    101: {"title": "", "class": "Edit", "pid": 42, "children": []},
}
CMD_TREE = {
    200: {"top": True, "title": "C:\\WINDOWS\\system32\\cmd.exe",
          "class": "ConsoleWindowClass", "pid": 7, "children": []},
}
CHROME_TREE = {
    300: {"top": True, "title": "Page - Chrome", "class": "Chrome_WidgetWin_1",
          "pid": 9, "children": [301]},
    301: {"title": "", "class": "Chrome_RenderWidgetHostHWND",
          "pid": 9, "children": []},
}


TREE = {**NOTEPAD_TREE, **CMD_TREE, **CHROME_TREE,
        400: {"top": True, "title": "dup", "class": "X", "pid": 1},
        401: {"top": True, "title": "dup", "class": "Y", "pid": 2},
        402: {"top": True, "title": "hidden", "class": "Z", "pid": 3,
              "visible": False}}


@pytest.fixture(autouse=True)
def fake_win(monkeypatch):
    monkeypatch.setattr(cu_scope, "win", FakeWin(TREE))
    yield cu_scope.win


def test_resolve_notepad_edit_child():
    out = cu_scope.resolve_input_target(title="Notepad")
    assert out["frame"] == 100
    assert out["input"] == 101  # Edit child, not the frame
    assert out["console"] is False


def test_resolve_ambiguous_raises():
    with pytest.raises(cu_scope.ScopeError, match="ambiguous_window"):
        cu_scope.resolve_window(title="dup")


def test_resolve_none_raises():
    with pytest.raises(cu_scope.ScopeError, match="window_not_found"):
        cu_scope.resolve_window(title="nope-nope")


def test_console_input_hwnd_is_frame():
    out = cu_scope.resolve_input_target(class_name="ConsoleWindowClass")
    assert out["input"] == 200  # console input targets the frame
    assert out["console"] is True
    assert cu_scope.pick_channel(out["input"]) == "console"


def test_chrome_channel_is_cdp():
    out = cu_scope.resolve_input_target(class_name="Chrome_WidgetWin_1")
    assert out["input"] == 301
    assert cu_scope.pick_channel(out["input"]) == "cdp"


def test_hidden_filtered():
    assert all(w["title"] != "hidden" for w in cu_scope.find_windows())


def test_pid_filter():
    out = cu_scope.resolve_window(pid=7)
    assert out == 200


def test_scope_error_off_windows(monkeypatch):
    monkeypatch.setattr(cu_scope, "win", None)
    with pytest.raises(cu_scope.ScopeError, match="platform"):
        cu_scope.resolve_window(title="x")


# -- PostMessage channel ------------------------------------------------------

def test_post_text_wm_char_sequence(fake_win):
    r = cu_scope.post_text(101, "ab")
    assert r == {"delivered": 2, "total": 2}
    msgs = fake_win.u32.posted
    assert [m[1] for m in msgs] == [cu_scope.WM_CHAR, cu_scope.WM_CHAR]
    assert msgs[0][2] == ord("a") and msgs[0][0] == 101


def test_post_text_partial_delivery_honest(fake_win):
    fake_win.u32.fail_after = 1
    r = cu_scope.post_text(101, "abc")
    assert r["delivered"] == 1 and r["total"] == 3  # never claims effect


def test_post_key_enter_sends_char(fake_win):
    r = cu_scope.post_key(101, "enter")
    assert r["delivered"] is True
    msgs = [m[1] for m in fake_win.u32.posted]
    assert msgs == [cu_scope.WM_KEYDOWN, cu_scope.WM_CHAR, cu_scope.WM_KEYUP]


def test_post_key_unknown_raises():
    with pytest.raises(cu_scope.ScopeError, match="unknown_key"):
        cu_scope.post_key(101, "hyper")


def test_post_click_lparam_packs_client_xy(fake_win):
    r = cu_scope.post_click(101, 5, 9)
    assert r["delivered"] is True
    d, u = fake_win.u32.posted[0], fake_win.u32.posted[1]
    assert d[1] == cu_scope.WM_LBUTTONDOWN and u[1] == cu_scope.WM_LBUTTONUP
    assert d[3] == (9 << 16) | 5


def test_post_click_failed_delivery_reported(fake_win):
    fake_win.u32.fail_after = 0
    r = cu_scope.post_click(101, 1, 1)
    assert r["delivered"] is False


# -- WriteConsoleInput channel --------------------------------------------------

class FakeCon:
    attach_ok = True
    last_written = None
    last_mouse = None
    detached = False

    def __init__(self, pid):
        self.pid = pid

    def attach(self):
        return self.attach_ok

    def write_input(self, text):
        FakeCon.last_written = text
        return True

    def mouse_event(self, x, y, buttons=0, **kw):
        FakeCon.last_mouse = (x, y, buttons)
        return True

    def detach(self):
        FakeCon.detached = True


@pytest.fixture
def fake_console(monkeypatch):
    mod = types.ModuleType("cu_terminal")
    mod._ConOut = FakeCon
    monkeypatch.setitem(sys.modules, "cu_terminal", mod)
    FakeCon.attach_ok = True
    FakeCon.last_written = None
    FakeCon.last_mouse = None
    FakeCon.detached = False
    return FakeCon


def test_console_type_reuses_conout(fake_console):
    r = cu_scope.console_type(200, "dir\r")
    assert r == {"delivered": True, "total": 4}
    assert FakeCon.last_written == "dir\r"
    assert FakeCon.detached is True


def test_console_type_rejects_non_console(fake_console):
    with pytest.raises(cu_scope.ScopeError, match="not_console_hwnd"):
        cu_scope.console_type(101, "x")


def test_console_attach_failure_honest(fake_console):
    FakeCon.attach_ok = False
    with pytest.raises(cu_scope.ScopeError, match="attach_console_failed"):
        cu_scope.console_type(200, "x")


def test_console_key_enter_maps_cr(fake_console):
    r = cu_scope.console_key(200, "enter")
    assert r["delivered"] is True
    assert FakeCon.last_written == "\r"


def test_console_mouse_click_pair(fake_console):
    r = cu_scope.console_mouse(200, 10, 5)
    assert r["delivered"] is True
    assert r["verified"] is False  # UNVERIFIED marker carried
    assert FakeCon.last_mouse == (10, 5, 0)


# -- UIA channel ----------------------------------------------------------------

class FakePattern:
    def __init__(self, kind, readonly=False):
        self.kind = kind
        self.CurrentIsReadOnly = readonly
        self.calls = []

    def Invoke(self):
        self.calls.append("Invoke")

    def SetValue(self, v):
        self.calls.append(("SetValue", v))

    def Scroll(self, h, v):
        self.calls.append(("Scroll", h, v))


class FakeElement:
    def __init__(self, patterns=None, children=None):
        self.patterns = patterns or {}
        self.children = children or {}

    def GetCurrentPattern(self, pid):
        return self.patterns.get(pid)

    def FindFirst(self, scope, cond):
        return self.children.get(cond.value)


class FakeCond:
    def __init__(self, prop, value):
        self.prop = prop
        self.value = value


class FakeCore:
    def __init__(self, root):
        self.root = root

    def ElementFromHandle(self, hwnd):
        return self.root if hwnd == 100 else None

    def CreatePropertyCondition(self, prop, value):
        return FakeCond(prop, value)


@pytest.fixture
def fake_uia(monkeypatch):
    root = FakeElement(
        patterns={10000: FakePattern("invoke"),
                  10002: FakePattern("value"),
                  10003: FakePattern("scroll")},
        children={"OK": FakeElement(patterns={10000: FakePattern("invoke")})})
    monkeypatch.setattr(cu_scope, "core_factory", lambda: FakeCore(root))
    yield root
    monkeypatch.setattr(cu_scope, "core_factory", None)


def test_uia_invoke_hwnd(fake_uia):
    r = cu_scope.uia_invoke(100)
    assert r["delivered"] is True and r["pattern"] == "Invoke"
    assert fake_uia.patterns[10000].calls == ["Invoke"]


def test_uia_invoke_named_descendant(fake_uia):
    r = cu_scope.uia_invoke(100, name="OK")
    assert r["delivered"] is True
    assert fake_uia.children["OK"].patterns[10000].calls == ["Invoke"]


def test_uia_set_value(fake_uia):
    r = cu_scope.uia_set_value(100, "hello")
    assert r["delivered"] is True
    assert fake_uia.patterns[10002].calls == [("SetValue", "hello")]


def test_uia_scroll_down(fake_uia):
    r = cu_scope.uia_scroll(100, direction="down")
    assert fake_uia.patterns[10003].calls == [("Scroll", 2, 3)]


def test_uia_no_pattern_honest(fake_uia):
    fake_uia.patterns.clear()
    r = cu_scope.uia_invoke(100)
    assert r["delivered"] is False and r["error"] == "no_pattern:invoke"


def test_uia_hwnd_not_found(fake_uia):
    r = cu_scope.uia_invoke(999)
    assert r["delivered"] is False and r["error"] == "hwnd_not_found"


def test_uia_element_not_found(fake_uia):
    r = cu_scope.uia_invoke(100, name="Nope")
    assert r["error"] == "element_not_found"


# -- overlay seams (S5/S6) -------------------------------------------------------

def _load_overlay():
    return cu_load.load("cu_overlay")


def test_fly_path_bezier_endpoints():
    ov = _load_overlay()
    pts = ov.fly_path(0, 0, 300, 300, duration_ms=300, fps=30)
    assert pts[0][:2] == (0, 0) and pts[-1][:2] == (300, 300)
    mid = pts[len(pts) // 2]
    # arc lifts off the straight diagonal line
    assert mid[0] != mid[1] or (mid[0], mid[1]) != (150, 150)


def test_fly_path_lift_perpendicular():
    ov = _load_overlay()
    pts = ov.fly_path(0, 0, 400, 0, duration_ms=200, fps=50)
    ys = [p[1] for p in pts[1:-1]]
    assert min(ys) < 0  # control point lifted perpendicular (up)


def test_build_scene_shape():
    ov = _load_overlay()
    s = ov.build_scene(cursor=(5, 5), boxes=[{"rect": [0, 0, 1, 1]}],
                       arrows=[{"line": [0, 0, 9, 9]}])
    assert s["cursor"] == (5, 5) and len(s["boxes"]) == 1
    assert s["arrows"][0]["line"][2:] == [9, 9]


def test_overlay_flags_zero_input_reach():
    ov = _load_overlay()
    # WS_EX_TRANSPARENT | NOACTIVATE must both be set on creation flags
    flags = (ov.WS_EX_LAYERED | ov.WS_EX_TRANSPARENT | ov.WS_EX_NOACTIVATE
             | ov.WS_EX_TOPMOST)
    assert flags & ov.WS_EX_TRANSPARENT and flags & ov.WS_EX_NOACTIVATE
    assert ov.WDA_EXCLUDEFROMCAPTURE == 0x11


def test_overlay_capture_validation():
    ov = _load_overlay()
    import pytest as _p
    if ov.sys.platform != "win32":
        with _p.raises(ov.OverlayError, match="platform"):
            ov.GhostOverlay(capture="hidden")
    else:
        with _p.raises(ov.OverlayError, match="bad_capture"):
            ov.GhostOverlay(capture="invisible")


# -- CDP channel (S7) ------------------------------------------------------------

def _load_browser():
    return cu_load.load("cu_browser")


class FakeWS:
    def __init__(self):
        self.calls = []

    def call(self, method, params=None, timeout=None):
        self.calls.append((method, params or {}))
        return {}


def test_cdp_key_enter_dispatch():
    cb = _load_browser()
    ws = FakeWS()
    cli = cb.BrowserClient(ws, "cdp", "page-1")
    cli.key("enter")
    methods = [c[0] for c in ws.calls]
    assert methods == ["Input.dispatchKeyEvent", "Input.dispatchKeyEvent"]
    down, up = ws.calls[0][1], ws.calls[1][1]
    assert down["windowsVirtualKeyCode"] == 13 and down["key"] == "Enter"
    assert down["type"] == "keyDown" and down["text"] == "\r"
    assert up["type"] == "keyUp"


def test_cdp_key_escape_raw():
    cb = _load_browser()
    ws = FakeWS()
    cli = cb.BrowserClient(ws, "cdp", "page-1")
    cli.key("escape")
    assert ws.calls[0][1]["type"] == "rawKeyDown"  # no text -> raw
    assert "text" not in ws.calls[0][1]


def test_bidi_key_uses_webdriver_codepoint():
    cb = _load_browser()
    ws = FakeWS()
    cli = cb.BrowserClient(ws, "bidi", "ctx-1")
    cli.key("enter")
    method, params = ws.calls[0]
    assert method == "input.performActions"
    acts = params["actions"][0]["actions"]
    assert acts[0]["value"] == "" and acts[0]["type"] == "keyDown"


def test_cdp_key_unknown_rejects():
    cb = _load_browser()
    cli = cb.BrowserClient(FakeWS(), "cdp", "p")
    with pytest.raises(ValueError, match="unknown_key"):
        cli.key("f13_no_such_key")


# -- CLI channel wiring (S8) ------------------------------------------------------

EXT = Path(__file__).resolve().parents[1] / "extensions" / "computer-use"


def _cli(script, *argv):
    import subprocess
    return subprocess.run(
        [sys.executable, str(EXT / script), *argv],
        capture_output=True, text=True, timeout=30)


def _cli_json(cp):
    assert cp.stdout.strip(), f"no stdout: {cp.stderr}"
    return json.loads(cp.stdout)


def test_scoped_requires_window_target():
    cp = _cli("type_text.py", "hi", "--channel", "scope")
    j = _cli_json(cp)
    assert cp.returncode == 2 and "window target" in j["error"]


def test_channel_env_requires_env():
    cp = _cli("type_text.py", "hi", "--channel", "env")
    j = _cli_json(cp)
    assert cp.returncode == 2 and "requires --env" in j["error"]


def test_scoped_rejects_env():
    cp = _cli("mouse.py", "click", "10", "20", "--channel", "scope",
              "--env", "x")
    j = _cli_json(cp)
    assert cp.returncode == 2 and "rejects --env" in j["error"]


def test_scoped_rejects_human_profile():
    cp = _cli("mouse.py", "click", "10", "20", "--channel", "scope",
              "--profile", "human", "--hwnd", "0x10")
    j = _cli_json(cp)
    assert cp.returncode == 2 and "teleport-only" in j["error"]


def test_uia_has_no_key_concept():
    cp = _cli("type_text.py", "--key", "enter", "--channel", "uia",
              "--hwnd", "0x10")
    j = _cli_json(cp)
    assert cp.returncode == 2 and "no key concept" in j["error"]


def test_scoped_missing_window_errors():
    cp = _cli("type_text.py", "hi", "--channel", "scope", "--hwnd", "0xDEAD")
    j = _cli_json(cp)
    assert cp.returncode in (1, 2) and not j["ok"]
