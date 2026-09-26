#!/usr/bin/env python3
"""Scoped window targeting for computer-use (F3).

A *window target* is an HWND resolved by title/class/pid, a different axis
from cu_target.py's *env* resolution (which picks an input universe:
local vs QMP backend). Window targets feed channels that never touch the
global input stream: PostMessage (`scope`), UIA patterns (`uia`),
WriteConsoleInput (`console`), CDP (`cdp`, browser only).

Honesty contract: delivery != effect. PostMessage bypasses the input queue
(no hooks, no shift-state, no IME); results report `delivered`, never
`clicked`/`typed`. Windows-only; every function degrades to a typed error
off-Windows so tests can run on any platform via the `win` seam.
"""
import ctypes
import json
import os
import re
import sys
from ctypes import wintypes

# -- input-bearing child classes worth descending into ----------------------
INPUT_CLASSES = {
    "edit", "richedit", "richedit20a", "richedit20w", "richedit50w",
    "richedit60w", "richeditbox", "scintilla", "termcontrol",
    "chrome_renderwidgethosthwnd", "microsoft.ui.content.contentwindowexportsite",
}
CONHOST_CLASS = "consolewindowclass"


class ScopeError(Exception):
    """Typed failure - carries a stable reason token for JSON errors."""


# -- Win32 backend seam ------------------------------------------------------
class _Win32:
    """Thin ctypes wrapper; tests swap `win` for a fake tree."""

    def __init__(self):
        if sys.platform != "win32":
            raise ScopeError("platform:scope_requires_windows")
        self.u32 = ctypes.windll.user32
        self.k32 = ctypes.windll.kernel32
        self._enum_proc = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def enum_top(self):
        out = []
        self.u32.EnumWindows(self._enum_proc(lambda h, _:
                                             out.append(int(h)) or True), 0)
        return out

    def enum_children(self, hwnd):
        out = []
        self.u32.EnumChildWindows(
            int(hwnd), self._enum_proc(lambda h, _: out.append(int(h)) or True), 0)
        return out

    def title(self, hwnd):
        n = self.u32.GetWindowTextLengthW(int(hwnd))
        buf = ctypes.create_unicode_buffer(n + 1)
        self.u32.GetWindowTextW(int(hwnd), buf, n + 1)
        return buf.value

    def class_name(self, hwnd):
        buf = ctypes.create_unicode_buffer(256)
        self.u32.GetClassNameW(int(hwnd), buf, 256)
        return buf.value

    def pid(self, hwnd):
        pid = ctypes.c_ulong(0)
        self.u32.GetWindowThreadProcessId(int(hwnd), ctypes.byref(pid))
        return pid.value

    def visible(self, hwnd):
        return bool(self.u32.IsWindowVisible(int(hwnd)))

    def rect(self, hwnd):
        r = wintypes.RECT()
        if not self.u32.GetWindowRect(int(hwnd), ctypes.byref(r)):
            raise ScopeError(f"no_rect:{hwnd}")
        return (r.left, r.top, r.right, r.bottom)


win = None
if sys.platform == "win32":
    try:
        win = _Win32()
    except Exception:
        win = None


def _need_win():
    if win is None:
        raise ScopeError("platform:scope_requires_windows")
    return win


# -- window-target resolution -------------------------------------------------
def window_info(hwnd):
    w = _need_win()
    return {"hwnd": int(hwnd), "pid": w.pid(hwnd),
            "class": w.class_name(hwnd), "title": w.title(hwnd),
            "visible": w.visible(hwnd), "rect": w.rect(hwnd)}


def find_windows(title=None, class_name=None, pid=None,
                 title_regex=False, visible_only=True):
    """Top-level windows matching the given filters."""
    w = _need_win()
    rx = re.compile(title, re.IGNORECASE) if (title and title_regex) else None
    out = []
    for h in w.enum_top():
        if visible_only and not w.visible(h):
            continue
        t, c, p = w.title(h), w.class_name(h), w.pid(h)
        if pid is not None and p != pid:
            continue
        if class_name is not None and c.lower() != class_name.lower():
            continue
        if title is not None:
            if rx:
                if not rx.search(t):
                    continue
            elif title.lower() not in t.lower():
                continue
        out.append({"hwnd": h, "pid": p, "class": c, "title": t})
    return out


def resolve_window(title=None, class_name=None, pid=None,
                   title_regex=False):
    """Exactly one top-level match required."""
    matches = find_windows(title=title, class_name=class_name, pid=pid,
                           title_regex=title_regex)
    if not matches:
        raise ScopeError("window_not_found")
    if len(matches) > 1:
        raise ScopeError("ambiguous_window:" +
                         ",".join(str(m["hwnd"]) for m in matches))
    return matches[0]["hwnd"]


def is_conhost(hwnd):
    return _need_win().class_name(hwnd).lower() == CONHOST_CLASS


def is_console(hwnd):
    """conhost family: ConsoleWindowClass (or PseudoConsole)."""
    return is_conhost(hwnd)


def input_hwnd(hwnd):
    """The HWND that actually receives input for a window target.

    Consoles take input via WriteConsoleInput on the frame. For everything
    else, descend to the deepest child whose class is an input class;
    fall back to the frame itself."""
    w = _need_win()
    if is_console(hwnd):
        return hwnd
    node = hwnd
    while True:
        children = w.enum_children(node)
        nxt = next((c for c in children
                    if w.class_name(c).lower() in INPUT_CLASSES), None)
        if nxt is None:
            return node
        node = nxt


def resolve_input_target(title=None, class_name=None, pid=None,
                         title_regex=False):
    """Full resolution: top-level window -> input-bearing HWND."""
    hwnd = resolve_window(title=title, class_name=class_name, pid=pid,
                          title_regex=title_regex)
    target = input_hwnd(hwnd)
    return {"frame": hwnd, "input": target, "console": is_console(hwnd),
            "info": window_info(hwnd)}


# -- PostMessage channel (S2) ---------------------------------------------------
WM_KEYDOWN, WM_KEYUP, WM_CHAR = 0x0100, 0x0101, 0x0102
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_RBUTTONDOWN, WM_RBUTTONUP = 0x0204, 0x0205
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 0x0001

VK = {"enter": 0x0D, "tab": 0x09, "escape": 0x1B, "esc": 0x1B,
      "backspace": 0x08, "delete": 0x2E, "space": 0x20,
      "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
      "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
      **{f"f{i}": 0x6F + i for i in range(1, 13)}}


def _post(hwnd, msg, wp, lp):
    """True only when the message was *delivered* to the queue.
    Delivery is not effect: posted input bypasses the queue (no hooks,
    no shift state); the app may still ignore it [F3 §1]."""
    w = _need_win()
    return bool(w.u32.PostMessageW(int(hwnd), msg, int(wp), int(lp)))


def post_text(hwnd, text):
    """WM_CHAR per char - the ControlSend-equivalent path for gullible
    Win32 controls. Returns {"delivered": n, "total": n}."""
    sent = 0
    for ch in text:
        if not _post(hwnd, WM_CHAR, ord(ch), 0):
            break
        sent += 1
    return {"delivered": sent, "total": len(text)}


def post_key(hwnd, key):
    """Named key via WM_KEYDOWN/UP + WM_CHAR for printable keys."""
    k = key.lower()
    if k not in VK:
        raise ScopeError(f"unknown_key:{key}")
    vk = VK[k]
    ok = _post(hwnd, WM_KEYDOWN, vk, 0)
    if ok and k == "enter":
        _post(hwnd, WM_CHAR, 0x0D, 0)
    if ok and k == "space":
        _post(hwnd, WM_CHAR, 0x20, 0)
    ok = _post(hwnd, WM_KEYUP, vk, 0) and ok
    return {"delivered": ok, "key": k}


def post_click(hwnd, x, y, button="left"):
    """Button down/up at client coords in lParam. Bypasses hit-testing and
    cursor position; effect is app-dependent [F3 §1]."""
    lp = ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)
    if button == "right":
        d, u = WM_RBUTTONDOWN, WM_RBUTTONUP
    else:
        d, u = WM_LBUTTONDOWN, WM_LBUTTONUP
    down = _post(hwnd, d, MK_LBUTTON, lp)
    up = _post(hwnd, u, 0, lp)
    return {"delivered": bool(down and up), "button": button,
            "client": [int(x), int(y)]}


def screen_to_client(hwnd, x, y):
    w = _need_win()
    pt = wintypes.POINT(int(x), int(y))
    if not w.u32.ScreenToClient(int(hwnd), ctypes.byref(pt)):
        raise ScopeError(f"screen_to_client_failed:{hwnd}")
    return pt.x, pt.y


# -- WriteConsoleInput channel (S3) ---------------------------------------------
def _console_handle(hwnd):
    """Attach to the console owning this HWND via cu_terminal's _ConOut.
    Returns the attached object; caller MUST call .detach()."""
    if not is_console(hwnd):
        raise ScopeError("not_console_hwnd:" + str(hwnd))
    pid = _need_win().pid(hwnd)
    import cu_terminal
    con = cu_terminal._ConOut(pid)
    if not con.attach():
        raise ScopeError(f"attach_console_failed:pid={pid}")
    return con


def console_type(hwnd, text):
    """Type text into a conhost console via KEY_EVENT records."""
    con = _console_handle(hwnd)
    try:
        ok = con.write_input(text)
        return {"delivered": bool(ok), "total": len(text)}
    finally:
        con.detach()


def console_key(hwnd, key):
    """Named key into a console. Enter maps to CR."""
    k = key.lower()
    if k == "enter":
        text = "\r"
    elif k == "tab":
        text = "\t"
    elif k == "escape" or k == "esc":
        text = "\x1b"
    else:
        raise ScopeError(f"console_key_unsupported:{key}")
    con = _console_handle(hwnd)
    try:
        ok = con.write_input(text)
        return {"delivered": bool(ok), "key": k}
    finally:
        con.detach()


def console_mouse(hwnd, x, y, click=True):
    """MOUSE_EVENT at console cell coords. UNVERIFIED [F3 gaps]: console
    mouse delivery may be focus-gated; report delivered, not effect."""
    con = _console_handle(hwnd)
    try:
        ok = True
        if click:
            ok = con.mouse_event(x, y, buttons=0x0001)  # FROM_LEFT_1ST_PRESSED
            ok = con.mouse_event(x, y, buttons=0x0000) and ok
        else:
            ok = con.mouse_event(x, y)
        return {"delivered": bool(ok), "pos": [int(x), int(y)],
                "verified": False,
                "note": "mouse focus gating UNVERIFIED"}
    finally:
        con.detach()


# -- UIA channel (S4) -----------------------------------------------------------
# Pattern IDs: UIA_InvokePatternId/Value/Scroll (control patterns act on
# provider semantics - background/occluded windows work [F3 §3]).
_PAT_INVOKE, _PAT_VALUE, _PAT_SCROLL = 10000, 10002, 10003
_PID_NAME = 30005
_SCOPE_DESC = 0x4
_SCROLL_AMT = {"up": 0, "down": 3, "left": 0, "right": 3,
               "small_up": 1, "small_down": 4, "small_left": 1,
               "small_right": 4, "page_up": 0, "page_down": 3}
_NO_SCROLL = 2  # ScrollAmount_NoAmount

core_factory = None  # test seam; default is cu_hints._uia_core


def _uia_call(hwnd, action, name=None, value=None, direction=None,
              timeout=4.0):
    """Run one UIA pattern on the target window (or a named descendant).
    Honest errors: element_not_found / no_pattern / readonly / timeout.
    Effect is provider-side, not input-pipeline - safe on background
    windows, but only where a real pattern exists."""
    import queue
    import threading

    def impl():
        if core_factory is not None:
            core = core_factory()
        else:
            import cu_hints
            core = cu_hints._uia_core()
        target = core.ElementFromHandle(hwnd)
        if target is None:
            return None, "hwnd_not_found"
        if name:
            cond = core.CreatePropertyCondition(_PID_NAME, name)
            target = target.FindFirst(_SCOPE_DESC, cond)
            if target is None:
                return None, "element_not_found"
        if action == "invoke":
            pat = target.GetCurrentPattern(_PAT_INVOKE)
            if pat is None:
                return None, "no_pattern:invoke"
            pat.Invoke()
            return {"pattern": "Invoke"}, None
        if action == "set_value":
            pat = target.GetCurrentPattern(_PAT_VALUE)
            if pat is None:
                return None, "no_pattern:value"
            if getattr(pat, "CurrentIsReadOnly", False):
                return None, "readonly"
            pat.SetValue(value)
            return {"pattern": "Value"}, None
        if action == "scroll":
            pat = target.GetCurrentPattern(_PAT_SCROLL)
            if pat is None:
                return None, "no_pattern:scroll"
            d = (direction or "down").lower()
            if d not in _SCROLL_AMT:
                return None, f"bad_direction:{direction}"
            amt = _SCROLL_AMT[d]
            horiz = amt if d in ("left", "right", "small_left",
                                 "small_right") else _NO_SCROLL
            vert = amt if d not in ("left", "right", "small_left",
                                    "small_right") else _NO_SCROLL
            pat.Scroll(horiz, vert)
            return {"pattern": "Scroll", "direction": d}, None
        return None, f"bad_action:{action}"

    q = queue.Queue(maxsize=1)

    def run():
        try:
            if core_factory is not None:
                q.put(impl())
            else:
                import cu_hints
                q.put(cu_hints._com_thread(impl))
        except Exception as exc:
            q.put((None, f"error:{type(exc).__name__}:{exc}"))

    threading.Thread(target=run, daemon=True).start()
    try:
        res = q.get(timeout=timeout)
    except queue.Empty:
        return None, "timeout"
    if res is None:
        return None, "error"
    return res


def _wrap(res, err):
    return {"delivered": res is not None, **(res or {}), "error": err}


def uia_invoke(hwnd, name=None, timeout=4.0):
    return _wrap(*_uia_call(hwnd, "invoke", name=name, timeout=timeout))


def uia_set_value(hwnd, value, name=None, timeout=4.0):
    return _wrap(*_uia_call(hwnd, "set_value", name=name, value=value,
                            timeout=timeout))


def uia_scroll(hwnd, direction="down", name=None, timeout=4.0):
    return _wrap(*_uia_call(hwnd, "scroll", name=name, direction=direction,
                            timeout=timeout))


# -- CDP channel (S7) ------------------------------------------------------------
# Bound-browser semantic path via cu_browser (loopback-pinned _cdp_client).
# Attach requires the browser launched with its debug port
# (--remote-debugging-port for Chromium) and bound via cu_browser.bind.

def cdp_click(hwnd, x, y, timeout=10.0):
    import cu_browser
    res, err = cu_browser.dom_action(hwnd, x, y, "click", timeout=timeout)
    return _wrap(res, err)


def cdp_type(hwnd, x, y, text, timeout=10.0):
    import cu_browser
    res, err = cu_browser.dom_action(hwnd, x, y, "type", text=text,
                                     timeout=timeout)
    return _wrap(res, err)


def cdp_key(hwnd, name, timeout=10.0):
    import cu_browser
    res, err = cu_browser.dom_key(hwnd, name, timeout=timeout)
    return _wrap(res, err)


def cdp_text(hwnd, text, timeout=10.0):
    """Insert text at the focused element - no click, no coords needed."""
    import cu_browser
    ok, reason = cu_browser.check(hwnd)
    if not ok:
        return _wrap(None, f"browser_{reason}")
    cli = cu_browser._cdp_client(timeout=timeout)
    if cli is None:
        return _wrap(None, "browser_unavailable")
    try:
        cli.insert_text(text)
        return {"delivered": True, "typed": len(text),
                "dialect": cli.dialect, "error": None}
    except Exception as exc:
        return _wrap(None, f"dom_{type(exc).__name__}:{exc}")
    finally:
        cli.close()


# -- ghost cursor (S5/S6 hookup) -----------------------------------------------
def ghost_to(hwnd, x, y, capture="visible", duration_ms=500):
    """Fly the ghost sprite to client-coords (x, y) of hwnd. The overlay
    never receives input; it only *shows* intent [F4 mechanism]."""
    import cu_overlay
    w = _need_win()
    pt = wintypes.POINT(int(x), int(y))
    if not w.u32.ClientToScreen(int(hwnd), ctypes.byref(pt)):
        raise ScopeError(f"client_to_screen_failed:{hwnd}")
    ov = cu_overlay.GhostOverlay(capture=capture)
    ov.start()
    try:
        ov.fly_to(pt.x, pt.y, duration_ms=duration_ms, then_hold_ms=350)
    finally:
        ov.close()
    return {"ghost": [pt.x, pt.y], "capture": capture}


# -- channel dispatch ----------------------------------------------------------
CHANNELS = ("scope", "uia", "console", "cdp")
CLI_CHANNELS = ("host", "env") + CHANNELS


def add_channel_args(sp):
    """Inject --channel/window-target/ghost flags into a subparser."""
    sp.add_argument("--channel", choices=CLI_CHANNELS, default="host",
                    help="input universe: host (default, global input) | "
                         "env (requires --env ID, remote backend) | scoped "
                         "channels scope/uia/console/cdp (window-targeted, "
                         "never touch global input)")
    sp.add_argument("--hwnd", default=None,
                    help="window target HWND (decimal or 0x)")
    sp.add_argument("--title", default=None, help="window target title")
    sp.add_argument("--title-regex", action="store_true")
    sp.add_argument("--class-name", default=None)
    sp.add_argument("--pid", type=int, default=None)
    sp.add_argument("--uia-name", default=None,
                    help="named descendant for uia channel (Invoke/Value "
                         "on the element, not the frame)")
    sp.add_argument("--cursor", choices=["real", "ghost"], default="real",
                    help="ghost = overlay sprite shows intent; the real "
                         "cursor never moves")
    sp.add_argument("--overlay-capture", choices=["visible", "hidden"],
                    default="visible",
                    help="hidden excludes the overlay from screen capture "
                         "(Win10 2004+); agent evidence frames go blind")


def pre_channel_check(argv, fail):
    """Channel/env legality BEFORE cli_guard claims --env. Scoped channels
    + --env must die here or cli_guard would silently take the env path."""
    import argparse
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--channel", default="host")
    pre.add_argument("--env", default=None)
    ns, _ = pre.parse_known_args(argv)
    if ns.channel == "env" and not ns.env:
        fail("--channel env requires --env ID", 2)
    if ns.env and ns.channel not in ("host", "env", None):
        fail(f"--channel {ns.channel} rejects --env "
             "(env is a separate universe)", 2)


def check_channel_args(args, fail):
    """Enforce channel semantics. `fail` prints JSON error and exits.
    Returns the channel actually selected."""
    ch = getattr(args, "channel", "host") or "host"
    env = getattr(args, "env", None)
    if ch == "env":
        if not env:
            fail("--channel env requires --env ID", 2)
        return ch  # existing remote path owns env dispatch
    if env:
        fail(f"--channel {ch} rejects --env (env is a separate universe)", 2)
    if ch == "host":
        if getattr(args, "cursor", "real") == "ghost":
            fail("--cursor ghost has no meaning on the host channel", 2)
        return ch
    # scoped channel
    prof = getattr(args, "profile", None)
    if prof in ("human", "smooth"):
        fail(f"--channel {ch} is teleport-only: --profile {prof} is "
             "host-only (human/smooth move a REAL cursor)", 2)
    if not any([getattr(args, "hwnd", None), getattr(args, "title", None),
                getattr(args, "class_name", None),
                getattr(args, "pid", None)]):
        fail(f"--channel {ch} needs a window target "
             "(--hwnd/--title/--class-name/--pid)", 2)
    return ch


def scoped_hwnd(args):
    """Resolve the input-bearing HWND for a scoped channel."""
    raw = getattr(args, "hwnd", None)
    if raw:
        frame = int(str(raw), 0)
    else:
        frame = resolve_window(title=getattr(args, "title", None),
                               class_name=getattr(args, "class_name", None),
                               pid=getattr(args, "pid", None),
                               title_regex=getattr(args, "title_regex",
                                                   False))
    return frame, input_hwnd(frame)


def ghost_if(args, hwnd, x, y):
    """Run the ghost fly-to when --cursor ghost; returns dict or None."""
    if getattr(args, "cursor", "real") != "ghost":
        return None
    return ghost_to(hwnd, x, y,
                    capture=getattr(args, "overlay_capture", "visible"))


def pick_channel(hwnd):
    """Suggested channel for a resolved HWND (app-class matrix, F3 §9)."""
    w = _need_win()
    c = w.class_name(hwnd).lower()
    if c == CONHOST_CLASS or c.startswith("pseudoconsole"):
        return "console"
    if c.startswith("chrome_"):
        return "cdp"       # message-level input is filtered by Chromium
    return "scope"         # uia is the safer default; caller may prefer it


def main():
    """Introspection CLI: resolve a window target, print JSON."""
    import argparse
    ap = argparse.ArgumentParser(prog="cu_scope.py")
    ap.add_argument("--title", default=None)
    ap.add_argument("--title-regex", action="store_true")
    ap.add_argument("--class-name", default=None)
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    try:
        if args.list:
            print(json.dumps({"ok": True, "windows": find_windows()}))
            return
        out = resolve_input_target(title=args.title, class_name=args.class_name,
                                   pid=args.pid, title_regex=args.title_regex)
        out["channel"] = pick_channel(out["input"])
        print(json.dumps({"ok": True, **out}))
    except ScopeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
