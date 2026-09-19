#!/usr/bin/env python3
"""Authorized-terminal read/control contract.

Terminal semantics are only ever allowed against a window the caller
explicitly bound for THIS automation session. Nothing here launches a
terminal, attaches to foreign consoles, or injects input anywhere the
binding didn't name.

    bind(hwnd, probe?)  -> writes the binding file (explicit, opt-in)
    unbind()            -> removes it
    binding()           -> dict | None
    check()             -> (allowed: bool, reason: str|None)

Modes (auto-detected by window class):
  wt      — Windows Terminal: UIA TextPattern full scrollback + physical input
  conhost — classic console: AttachConsole/CONOUT$ read + WriteConsoleInput
  mintty  — Git Bash: pixel read (screenshot) + physical input only

Binding lives in <temp>/devin-cu-terminal.json, session+TTL rules equal
to cu_browser's. Spawn mode (own PTY via pywinpty) is in-process and
never touches a user's terminal.
"""
import json
import os
import re
import sys
import tempfile
import threading
import time
import uuid
from collections import deque

import cu_hints

BINDING_TTL_S = float(os.environ.get("CU_TERMINAL_TTL", "600"))
_BINDING_OVERRIDE = None   # tests inject a path here
_SESSIONS_OVERRIDE = None  # tests inject a registry path here

MAX_OUTPUT = 16000
IDLE_POLLS = 4
POLL_S = 0.25

_CLASSES = {
    "CASCADIA_HOSTING_WINDOW_CLASS": "wt",
    "ConsoleWindowClass": "conhost",
    "mintty": "mintty",
}


# -- binding ------------------------------------------------------------------

def boundaries(text):
    """Wrap terminal-extracted text as untrusted content."""
    n = uuid.uuid4().hex[:8]
    return (f"--- BEGIN UNTRUSTED TERMINAL OUTPUT {n} ---\n{text}\n"
            f"--- END UNTRUSTED TERMINAL OUTPUT {n} ---")


def _path():
    if _BINDING_OVERRIDE:
        return _BINDING_OVERRIDE
    return os.path.join(tempfile.gettempdir(), "devin-cu-terminal.json")


def classify(class_name):
    if not class_name:
        return "unknown"
    if class_name in _CLASSES:
        return _CLASSES[class_name]
    if class_name.startswith("mintty"):
        return "mintty"
    return "unknown"


def detect(hwnd, probe=None):
    """Classify a window. probe: {hwnd: {class, pid, title}} — injectable."""
    probe = probe if probe is not None else _window_probe()
    info = probe.get(hwnd, {})
    cls = info.get("class", "")
    return {"hwnd": hwnd, "mode": classify(cls), "class": cls,
            "pid": info.get("pid", 0), "title": info.get("title", "")}


def bind(hwnd, mode="auto", probe=None):
    """Record an explicitly-authorized terminal window for this session."""
    if not isinstance(hwnd, int) or hwnd <= 0:
        return {"ok": False, "error": "hwnd must be a positive int"}
    d = detect(hwnd, probe=probe)
    if d["mode"] == "unknown":
        return {"ok": False,
                "error": f"unknown window class {d['class']!r} — "
                         "only wt/conhost/mintty supported"}
    if mode != "auto" and mode != d["mode"]:
        return {"ok": False,
                "error": f"forced mode {mode} != detected {d['mode']}"}
    data = {"hwnd": hwnd, "pid": d["pid"], "mode": d["mode"],
            "class": d["class"], "title": d["title"],
            "session_id": cu_hints.session_id(),
            "created_at": time.time()}
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, _path())
    return {"ok": True, "binding": data}


def unbind():
    try:
        os.remove(_path())
    except OSError:
        pass
    return {"ok": True}


def binding():
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if data.get("session_id") != cu_hints.session_id():
        return None
    if time.time() - data.get("created_at", 0) > BINDING_TTL_S:
        return None
    return data


def check():
    return (True, None) if binding() else (False, "no_binding")


# -- OS seams (lazy; fakeable) ---------------------------------------------------

def _window_probe():
    """{hwnd: {class, pid, title}} for visible windows — ctypes EnumWindows."""
    out = {}
    if os.name != "nt":
        return out
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32

    def cb(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        n = u.GetWindowTextLengthW(hwnd)
        tbuf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, tbuf, n + 1)
        pid = ctypes.c_ulong(0)
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        cn = ctypes.create_unicode_buffer(256)
        u.GetClassNameW(hwnd, cn, 256)
        out[hwnd] = {"class": cn.value, "pid": pid.value,
                     "title": tbuf.value}
        return True

    cb_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    u.EnumWindows(cb_t(cb), 0)
    return out


def _default_io():
    """Real OS-backed IO seam. Keys:
    termcontrols(hwnd)->[obj(.document_text(),.has_focus)],
    class_name(hwnd)->str, conout(pid)->_ConOut,
    focus(hwnd)->bool, kbd()->controller, screenshot_region(rect)->path."""
    return {
        "termcontrols": _uia_termcontrols,
        "class_name": _class_name,
        "conout": lambda pid: _ConOut(pid),
        "focus": _focus_hwnd,
        "kbd": _keyboard,
        "screenshot_region": _screenshot_region,
    }


def _class_name(hwnd):
    if os.name != "nt":
        return ""
    import ctypes
    cn = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetClassNameW(hwnd, cn, 256)
    return cn.value


class _TermControl:
    """Adapter over a UIA element exposing TextPattern."""

    def __init__(self, el, tp):
        self._el = el
        self._tp = tp

    @property
    def has_focus(self):
        try:
            return bool(self._el.CurrentHasKeyboardFocus)
        except Exception:
            return False

    def document_text(self):
        return self._tp.DocumentRange.GetText(-1)


def _uia_termcontrols(hwnd):
    """TermControl elements with TextPattern under hwnd — comtypes UIA."""
    if os.name != "nt":
        return []
    import comtypes.client
    comtypes.client.GetModule("UIAutomationCore.dll")
    uia_tlb = comtypes.gen.UIAutomationClient
    uia = comtypes.client.CreateObject(
        "{ff48dba4-60ef-4201-aa87-54103eef594e}",
        interface=uia_tlb.IUIAutomation)
    root = uia.ElementFromHandle(hwnd)
    cond = uia.CreatePropertyCondition(
        uia_tlb.UIA_IsTextPatternAvailablePropertyId, True)
    els = root.FindAll(uia_tlb.TreeScope_Subtree, cond)
    out = []
    for i in range(els.Length):
        el = els.GetElement(i)
        try:
            tp = el.GetCurrentPattern(
                uia_tlb.UIA_TextPatternId).QueryInterface(
                    uia_tlb.IUIAutomationTextPattern)
        except Exception:
            continue
        out.append(_TermControl(el, tp))
    return out


class _ConOut:
    """AttachConsole + CONOUT$/CONIN$ wrapper. Always detaches."""

    def __init__(self, pid):
        self.pid = pid
        self._k = None
        self._h_out = None
        self._h_in = None

    def attach(self, pid=None):
        import ctypes
        k = ctypes.windll.kernel32
        self._k = k
        # guard: never take console signals for ourselves
        k.SetConsoleCtrlHandler(None, True)
        k.FreeConsole()
        if not k.AttachConsole(pid or self.pid):
            return False
        ga = 0x80000000 | 0x40000000
        self._h_out = k.CreateFileW("CONOUT$", ga, 3, None, 3, 0, None)
        self._h_in = k.CreateFileW("CONIN$", ga, 3, None, 3, 0, None)
        return self._h_out not in (None, -1)

    def buffer_info(self):
        import ctypes
        from ctypes import wintypes

        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        class RECT(ctypes.Structure):
            _fields_ = [("L", ctypes.c_short), ("T", ctypes.c_short),
                        ("R", ctypes.c_short), ("B", ctypes.c_short)]

        class CSBI(ctypes.Structure):
            _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                        ("wAttributes", wintypes.WORD), ("srWindow", RECT),
                        ("dwMaximumWindowSize", COORD)]
        i = CSBI()
        if not self._k.GetConsoleScreenBufferInfo(self._h_out,
                                                  ctypes.byref(i)):
            return {}
        return {"cols": i.dwSize.X, "rows": i.dwSize.Y,
                "cursor": [i.dwCursorPosition.X, i.dwCursorPosition.Y],
                "window": [i.srWindow.L, i.srWindow.T,
                           i.srWindow.R, i.srWindow.B]}

    def read_lines(self):
        import ctypes
        from ctypes import wintypes
        info = self.buffer_info()
        cols, rows = info["cols"], info["rows"]
        k = self._k

        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        class RECT(ctypes.Structure):
            _fields_ = [("L", ctypes.c_short), ("T", ctypes.c_short),
                        ("R", ctypes.c_short), ("B", ctypes.c_short)]

        class CI(ctypes.Structure):
            _fields_ = [("Char", ctypes.c_wchar * 1),
                        ("Attributes", wintypes.WORD)]
        n = cols * rows
        buf = (CI * n)()
        rect = RECT(0, 0, cols - 1, rows - 1)
        if not k.ReadConsoleOutputW(self._h_out, buf, COORD(cols, rows),
                                    COORD(0, 0), ctypes.byref(rect)):
            return []
        return ["".join(buf[y * cols + x].Char[0]
                        for x in range(cols)).rstrip()
                for y in range(rect.T, rect.B + 1)]

    def write_input(self, text):
        """KEY_EVENT records (VK=0 + UnicodeChar) into CONIN$."""
        import ctypes
        from ctypes import wintypes
        k = self._k

        class KE(ctypes.Structure):
            _fields_ = [("bKeyDown", wintypes.BOOL),
                        ("wRepeatCount", wintypes.WORD),
                        ("wVirtualKeyCode", wintypes.WORD),
                        ("wVirtualScanCode", wintypes.WORD),
                        ("UnicodeChar", wintypes.WCHAR),
                        ("dwControlKeyState", wintypes.DWORD)]

        class U(ctypes.Union):
            _fields_ = [("KeyEvent", KE), ("Pad", ctypes.c_byte * 16)]

        class IR(ctypes.Structure):
            _fields_ = [("EventType", wintypes.WORD), ("Event", U)]
        for ch in text:
            recs = (IR * 2)()
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
            w = wintypes.DWORD(0)
            if not k.WriteConsoleInputW(self._h_in, recs, 2,
                                        ctypes.byref(w)):
                return False
        return True

    def detach(self):
        try:
            if self._k is not None:
                if self._h_out:
                    self._k.CloseHandle(self._h_out)
                if self._h_in:
                    self._k.CloseHandle(self._h_in)
                self._k.FreeConsole()
        except Exception:
            pass


def _focus_hwnd(hwnd):
    if os.name != "nt":
        return False
    import ctypes
    u = ctypes.windll.user32
    k = ctypes.windll.kernel32
    fg = u.GetForegroundWindow()
    tid_fg = u.GetWindowThreadProcessId(fg, None)
    tid_me = k.GetCurrentThreadId()
    u.AttachThreadInput(tid_me, tid_fg, True)
    u.SetForegroundWindow(hwnd)
    u.BringWindowToTop(hwnd)
    u.AttachThreadInput(tid_me, tid_fg, False)
    time.sleep(0.3)
    return u.GetForegroundWindow() == hwnd


def _keyboard():
    from pynput.keyboard import Controller
    return Controller()


def _screenshot_region(rect):
    """Crop the bound window region via mss — returns PNG path."""
    import mss
    import mss.tools
    x, y, w, h = rect
    with mss.mss() as sct:
        img = sct.grab({"left": x, "top": y, "width": w, "height": h})
        path = os.path.join(tempfile.gettempdir(),
                            f"devin-cu-term-{uuid.uuid4().hex[:8]}.png")
        mss.tools.to_png(img.rgb, img.size, output=path)
        return path


# -- read paths -----------------------------------------------------------------

def _window_rect(hwnd):
    import ctypes

    class R(ctypes.Structure):
        _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                    ("r", ctypes.c_long), ("b", ctypes.c_long)]
    r = R()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.l, r.t, r.r - r.l, r.b - r.t)


def _slice(text, tail=None, find=None):
    lines = text.splitlines()
    if find:
        hits = [i for i, l in enumerate(lines) if find.lower() in l.lower()]
        if hits:
            a, b = max(0, hits[0] - 3), min(len(lines), hits[-1] + 4)
            return "\n".join(lines[a:b]), len(hits)
        return "", 0
    if tail:
        return "\n".join(lines[-tail:]), None
    return text, None


def _read_wt(hwnd, io, tail=None, find=None):
    tcs = io["termcontrols"](hwnd)
    if not tcs:
        return {"ok": False, "error": "no_termcontrol"}
    tc = next((c for c in tcs if getattr(c, "has_focus", False)),
              tcs[0])
    text = tc.document_text()
    sliced, matches = _slice(text, tail=tail, find=find)
    out = {"ok": True, "mode": "wt", "text": boundaries(sliced),
           "chars": len(text)}
    if matches is not None:
        out["matches"] = matches
    return out


def _read_conhost(pid, io, tail=None, find=None):
    con = io["conout"](pid)
    try:
        if not con.attach(pid):
            return {"ok": False, "error": "attach_failed"}
        lines = con.read_lines()
    finally:
        con.detach()
    text = "\n".join(lines)
    sliced, matches = _slice(text, tail=tail, find=find)
    out = {"ok": True, "mode": "conhost", "text": boundaries(sliced),
           "chars": len(text)}
    if matches is not None:
        out["matches"] = matches
    return out


def _conhost_info(pid, io):
    con = io["conout"](pid)
    try:
        if not con.attach(pid):
            return {"ok": False, "error": "attach_failed"}
        i = con.buffer_info()
    finally:
        con.detach()
    return {"ok": True, **i}


def _conhost_send(pid, text, io):
    con = io["conout"](pid)
    try:
        if not con.attach(pid):
            return {"ok": False, "error": "attach_failed"}
        ok = con.write_input(text)
    finally:
        con.detach()
    return {"ok": bool(ok)}


def _read_mintty(hwnd, io):
    rect = _window_rect(hwnd)
    path = io["screenshot_region"](rect)
    return {"ok": True, "mode": "mintty", "image": path,
            "note": "mintty exposes no text channel — image only"}


def read(tail=None, find=None, io=None):
    ok, why = check()
    if not ok:
        return {"ok": False, "error": why}
    b = binding()
    io = io or _default_io()
    if b["mode"] == "wt":
        return _read_wt(b["hwnd"], io, tail=tail, find=find)
    if b["mode"] == "conhost":
        return _read_conhost(b["pid"], io, tail=tail, find=find)
    if b["mode"] == "mintty":
        return _read_mintty(b["hwnd"], io)
    return {"ok": False, "error": f"unsupported mode {b['mode']}"}


def info(io=None):
    ok, why = check()
    if not ok:
        return {"ok": False, "error": why}
    b = binding()
    out = {"ok": True, "mode": b["mode"], "hwnd": b["hwnd"],
           "pid": b["pid"], "title": b.get("title", "")}
    io = io or _default_io()
    if b["mode"] == "conhost":
        out.update(_conhost_info(b["pid"], io))
    return out


# -- control --------------------------------------------------------------------

_KEYS = {"enter": "\r", "tab": "\t", "esc": "\x1b"}


def _phys_type(hwnd, text, io):
    if not io["focus"](hwnd):
        return {"ok": False, "error": "focus_failed"}
    kb = io["kbd"]()
    kb.type(text)
    return {"ok": True}


def type_text(text, io=None):
    ok, why = check()
    if not ok:
        return {"ok": False, "error": why}
    b = binding()
    io = io or _default_io()
    if b["mode"] == "conhost":
        return _conhost_send(b["pid"], text, io)
    return _phys_type(b["hwnd"], text, io)


def key(name, io=None):
    ok, why = check()
    if not ok:
        return {"ok": False, "error": why}
    b = binding()
    io = io or _default_io()
    if b["mode"] == "conhost":
        ch = _KEYS.get(name)
        if ch is None and name == "ctrl+c":
            return _conhost_send(b["pid"], "\x03", io)
        if ch is None:
            return {"ok": False, "error": f"unknown key {name}"}
        return _conhost_send(b["pid"], ch, io)
    if not io["focus"](b["hwnd"]):
        return {"ok": False, "error": "focus_failed"}
    kb = io["kbd"]()
    from pynput.keyboard import Key
    table = {"enter": Key.enter, "tab": Key.tab, "esc": Key.esc,
             "up": Key.up, "down": Key.down, "left": Key.left,
             "right": Key.right}
    if name == "ctrl+c":
        with kb.pressed(Key.ctrl_l):
            kb.tap("c")
        return {"ok": True}
    k = table.get(name)
    if k is None:
        return {"ok": False, "error": f"unknown key {name}"}
    kb.tap(k)
    return {"ok": True}


def scroll(direction="up", n=3, io=None):
    ok, why = check()
    if not ok:
        return {"ok": False, "error": why}
    io = io or _default_io()
    b = binding()
    if not io["focus"](b["hwnd"]):
        return {"ok": False, "error": "focus_failed"}
    from pynput.mouse import Controller
    m = Controller()
    dy = n if direction == "up" else -n
    x, y, w, h = _window_rect(b["hwnd"])
    m.position = (x + w // 2, y + h // 2)
    m.scroll(0, dy)
    return {"ok": True}


# -- exec engine ------------------------------------------------------------------

_INPUT_RX = re.compile(
    r"(\(y/n\)|\[y/n\]|\(yes/no\)|password|passphrase|\(END\)|"
    r"press any key|continue\?)", re.I)

_SENTINELS = {
    "cmd": ' & echo {tag}:%ERRORLEVEL%',
    "powershell": ' ; echo "{tag}:$LASTEXITCODE"',
    "pwsh": ' ; echo "{tag}:$LASTEXITCODE"',
    "bash": ' ; echo {tag}:$?',
    "sh": ' ; echo {tag}:$?',
    "auto": ' ; echo {tag}:$?',
}


def _sentinel_cmd(shell, cmd, tag):
    tpl = _SENTINELS.get(shell, _SENTINELS["auto"])
    return cmd + tpl.format(tag=f"CU_EXIT_{tag}")


def _parse_exit(text, tag):
    m = re.search(rf"CU_EXIT_{re.escape(tag)}:(\d+)", text)
    if not m:
        return None, text
    return int(m.group(1)), re.sub(
        rf".*CU_EXIT_{re.escape(tag)}:\d+.*\r?\n?", "", text)


def _strip_echo(text, cmd):
    """Remove the echoed command line (wrap-tolerant, whitespace-insens)."""
    norm = re.sub(r"\s+", "", cmd)
    if not norm:
        return text
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        acc = ""
        j = i
        while j < len(lines) and len(acc) < len(norm):
            # strip the prompt-ish prefix from the first echo line
            seg = lines[j]
            acc += re.sub(r"\s+", "", seg)
            if norm in acc or acc.endswith(norm):
                del lines[i:j + 1]
                return "".join(lines)
            j += 1
        i += 1
    # fallback: first line containing the command
    for idx, l in enumerate(lines):
        if norm[:20] in re.sub(r"\s+", "", l):
            del lines[idx]
            break
    return "".join(lines)


_PROMPT_RX = re.compile(
    r"^\s*([A-Za-z]:[\\/>]|PS\s|[^ ]*[@:][^\r\n]*[$#>]\s*|>>>|\(end\))",
    re.I)


def _strip_prompt(text):
    lines = text.rstrip().splitlines()
    while lines and (not lines[-1].strip() or _PROMPT_RX.match(lines[-1])):
        lines.pop()
    sep = "\r\n" if "\r\n" in text else "\n"
    return sep.join(lines)


def _cap(text, max_chars=MAX_OUTPUT):
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _cap_spill(text, max_chars=MAX_OUTPUT):
    """Tail-cap; spill the full text to a temp file when capped."""
    if len(text) <= max_chars:
        return text, None
    path = os.path.join(tempfile.gettempdir(),
                        f"cu-term-{uuid.uuid4().hex[:8]}.log")
    try:
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            f.write(text)
    except OSError:
        path = None
    return text[-max_chars:], path


_ALT_BUFFER_RX = re.compile(r"\x1b\[\?1049h")


def _needs_input(tail):
    return bool(_INPUT_RX.search(tail.strip()[-200:]))


# -- command gate (deny-wins; confirm for injection-sensitive) -----------------

_DENY_RX = re.compile(
    r"^\s*(rm\b|del\b|erase\b|kill\b|format\b|shutdown\b|mkfs\b|"
    r"rmdir\b|rd\b|reg\s+delete|diskpart\b|taskkill\b|"
    r"Remove-Item\b|Stop-Process\b|Clear-Disk\b)", re.I)
_CONFIRM_RX = re.compile(
    r"^\s*(curl\b|wget\b|eval\b|iex\b|Invoke-Expression\b|"
    r"Invoke-WebRequest\b|bash\b|sh\b|cmd\b|powershell\b|pwsh\b|"
    r"start-process\b|sudo\b)", re.I)


def _check_command(cmd, confirm=False):
    """Split into subcommands; deny wins over everything."""
    parts = re.split(r"&&|\|\||;|\|", cmd)
    subs = [p.strip() for p in parts if p.strip()] or [cmd.strip()]
    denied = [s for s in subs if _DENY_RX.match(s)]
    if denied:
        return {"ok": False, "error": "denied",
                "denied": denied}
    risky = [s for s in subs if _CONFIRM_RX.match(s)]
    if risky and not confirm:
        return {"ok": False, "error": "confirm_required",
                "needs_confirm": risky}
    return {"ok": True, "subcommands": subs}


def _shell_of(b):
    t = (b.get("title") or "").lower()
    for s in ("pwsh", "powershell", "bash", "cmd", "mintty", "zsh", "sh"):
        if s in t:
            return {"powershell": "pwsh", "mintty": "bash"}.get(s, s)
    return {"wt": "pwsh", "conhost": "cmd", "mintty": "bash"}[b["mode"]]


def _raw_text(result):
    """Unwrap boundaries() for internal processing."""
    if not result.get("ok"):
        return ""
    t = result.get("text", "")
    t = re.sub(r"^--- BEGIN UNTRUSTED TERMINAL OUTPUT \w+ ---\n", "", t)
    t = re.sub(r"\n?--- END UNTRUSTED TERMINAL OUTPUT \w+ ---\s*$", "", t)
    return t


def send(cmd, shell=None, timeout=10.0, confirm=False, io=None):
    """Type cmd+sentinel on the bound terminal, wait for completion, return
    stripped capped output + exit code (or state flags)."""
    ok, why = check()
    if not ok:
        return {"ok": False, "error": why}
    gate = _check_command(cmd, confirm)
    if not gate["ok"]:
        return gate
    b = binding()
    io = io or _default_io()
    shell = shell or _shell_of(b)
    tag = uuid.uuid4().hex[:6]
    line = _sentinel_cmd(shell, cmd, tag)

    before = _raw_text(read(io=io))
    w = type_text(line + "\r", io=io)
    if not w.get("ok"):
        return w

    deadline = time.time() + timeout
    seen_cmd = False
    stable = 0
    last = ""
    exit_code, output, state = None, "", "timeout"
    while time.time() < deadline:
        time.sleep(POLL_S)
        cur = _raw_text(read(io=io))
        if cur != last:
            stable = 0
            last = cur
        else:
            stable += 1
        if not seen_cmd and cmd in cur:
            seen_cmd = True  # cursor moved past send point
        code, _clean = _parse_exit(cur, tag)
        if code is not None:
            exit_code, state = code, "completed"
            break
        if seen_cmd and stable >= IDLE_POLLS:
            state = "idle"
            break
    new = cur[len(before):] if cur.startswith(before) else cur
    clean = _strip_prompt(_strip_echo(new, line))
    clean = re.sub(rf".*CU_EXIT_{tag}:\d+.*\r?\n?", "", clean)
    output, spill = _cap_spill(clean.strip())
    if _needs_input(cur[-300:]):
        state = "input_needed"
    out = {"ok": True, "shell": shell, "state": state,
           "exit_code": exit_code, "output": boundaries(output),
           "chars": len(clean)}
    if spill:
        out["spill"] = spill
    return out


# -- spawn mode (own PTY — never touches user terminals) ------------------------

_SESSIONS = {}


def _pty_factory(shell, cols, rows):
    from winpty import PtyProcess, Backend
    return PtyProcess.spawn(shell, dimensions=(rows, cols),
                            backend=Backend.WinPTY)


_SPAWN_SHELLS = {"cmd", "powershell", "pwsh", "bash", "wsl", "sh"}


class _PtySession:
    """PTY + background reader accumulating output into a deque."""

    def __init__(self, pty):
        self.pty = pty
        self.buf = deque(maxlen=20000)
        self.lock = threading.Lock()
        self.alive = True
        self._t = threading.Thread(target=self._drain, daemon=True)
        self._t.start()

    def _drain(self):
        while True:
            try:
                d = self.pty.read()
            except Exception:
                break
            if not d:
                time.sleep(0.02)
                continue
            with self.lock:
                self.buf.append(d)

    def text(self):
        with self.lock:
            return "".join(self.buf)


def _sessions_path():
    if _SESSIONS_OVERRIDE:
        return _SESSIONS_OVERRIDE
    return os.path.join(tempfile.gettempdir(), "devin-cu-tsessions.json")


def _register(sid, meta):
    try:
        path = _sessions_path()
        try:
            reg = json.load(open(path, encoding="utf-8"))
        except Exception:
            reg = {}
        reg[sid] = meta
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reg, f)
        os.replace(tmp, path)
    except OSError:
        pass


def sessions():
    return {sid: s.meta for sid, s in _SESSIONS.items()}


def spawn(shell="cmd", cols=120, rows=30):
    if shell not in _SPAWN_SHELLS:
        return {"ok": False,
                "error": f"unsupported shell {shell!r} "
                         f"(allowed: {sorted(_SPAWN_SHELLS)})"}
    argv = {"cmd": "cmd.exe", "powershell": "powershell.exe",
            "pwsh": "pwsh.exe", "bash": "bash.exe",
            "wsl": "wsl.exe", "sh": "sh.exe"}[shell]
    env = None
    if shell == "wsl":
        env = dict(os.environ, WSL_UTF8="1")
    try:
        pty = _pty_factory([argv], cols, rows) if env is None else \
            _spawn_env(argv, cols, rows, env)
    except Exception as e:
        return {"ok": False, "error": f"spawn_failed: {type(e).__name__}: {e}"}
    sid = uuid.uuid4().hex[:10]
    s = _PtySession(pty)
    s.meta = {"shell": shell, "cols": cols, "rows": rows,
              "created_at": time.time()}
    _SESSIONS[sid] = s
    _register(sid, s.meta)
    return {"ok": True, "session": sid, "shell": shell}


def _spawn_env(argv, cols, rows, env):
    from winpty import PtyProcess, Backend
    return PtyProcess.spawn(argv, dimensions=(rows, cols),
                            backend=Backend.WinPTY, env=env)


def send_to(sid, text):
    s = _SESSIONS.get(sid)
    if s is None:
        return {"ok": False, "error": "unknown_session"}
    try:
        s.pty.write(text)
    except Exception as e:
        return {"ok": False, "error": f"write_failed: {e}"}
    return {"ok": True}


def recv_from(sid, tail=None, wait=None, timeout=10.0):
    s = _SESSIONS.get(sid)
    if s is None:
        return {"ok": False, "error": "unknown_session"}
    deadline = time.time() + timeout
    rx = re.compile(wait) if wait else None
    time.sleep(0.05)  # grace: let the reader thread land pending output
    while True:
        txt = s.text()
        if rx is None or rx.search(txt):
            break
        if time.time() >= deadline:
            return {"ok": False, "error": "timeout",
                    "output": boundaries(_cap(txt))}
        time.sleep(POLL_S)
    out = txt if tail is None else "\n".join(txt.splitlines()[-tail:])
    capped, spill = _cap_spill(out)
    r = {"ok": True, "output": boundaries(capped),
         "alive": s.pty.isalive()}
    if spill:
        r["spill"] = spill
    if _ALT_BUFFER_RX.search(txt):
        r["alt_buffer"] = True  # fullscreen app (vim/htop) — detach
    return r


def close_session(sid):
    s = _SESSIONS.pop(sid, None)
    if s is None:
        return {"ok": False, "error": "unknown_session"}
    try:
        s.pty.terminate()
    except Exception:
        pass
    s.alive = False
    try:
        path = _sessions_path()
        reg = json.load(open(path, encoding="utf-8"))
        reg.pop(sid, None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(reg, f)
    except Exception:
        pass
    return {"ok": True}


def kill(sid):
    s = _SESSIONS.get(sid)
    if s is None:
        return {"ok": False, "error": "unknown_session"}
    try:
        s.pty.terminate()
    except Exception as e:
        return {"ok": False, "error": f"kill_failed: {e}"}
    return {"ok": True}
