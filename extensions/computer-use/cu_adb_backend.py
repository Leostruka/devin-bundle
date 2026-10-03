#!/usr/bin/env python3
"""adb backend — Android device/emulator as an --env target.

Spec (.devin/computer-use/envs/<id>.json):
    {"env_id": "phone", "provider": "adb",
     "serial": "emulator-5554",          # optional when exactly one device
     "adb_path": "C:/.../adb.exe"}       # optional override; else $CU_ADB/PATH

Attach-only: no create/start/stop lifecycle (env.py rejects those for this
provider). Observation via `exec-out screencap`; input via `shell input`;
element tree via `uiautomator dump` (real nodes, not pixel guessing);
exec.run via `shell` — all replies are untrusted device data.
"""
import hashlib
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cu_target
from cu_qmp_backend import BackendError, parse_frame


class UnsupportedOp(Exception):
    """The op has no honest adb equivalent (no cursor, no chords)."""


class UnsupportedText(Exception):
    """Text outside what `input text` can deliver (non-ASCII, controls)."""


_KEYCODES = {
    "enter": 66, "tab": 61, "space": 62, "backspace": 67, "delete": 67,
    "up": 19, "down": 20, "left": 21, "right": 22,
    "esc": 4, "back": 4, "home_screen": 3,
    "move_home": 122, "end": 123, "pageup": 92, "pagedown": 93,
    "menu": 82, "search": 84,
}

_CLICKABLE_ATTRS = ("clickable", "long-clickable", "checkable", "scrollable")
_BOUNDS_RX = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def _safe_component(s):
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(s))


def _escape_input_text(text):
    """Escape for `adb shell input text`: % -> %25, space -> %s, then
    single-quote for the remote shell."""
    if not text or any(ord(c) < 32 or ord(c) > 126 for c in text):
        raise UnsupportedText(f"unsupported chars in {text!r} "
                              "(ascii printable only; use --key enter)")
    e = text.replace("%", "%25").replace(" ", "%s")
    return "'" + e.replace("'", "'\"'\"'") + "'"


def _png_path(env_dir):
    env_dir = Path(env_dir)
    env_dir.mkdir(parents=True, exist_ok=True)
    return env_dir / f"screendump-{time.monotonic_ns()}.png"


class AdbBackend:
    """Backend over the Android Debug Bridge. `run` is injectable in
    tests: run(argv_list, timeout_s) -> subprocess.CompletedProcess."""

    def __init__(self, env_id, spec, run=None):
        self.env_id = env_id
        self.spec = spec or {}
        self._run = run or self._default_run
        self._serial = self.spec.get("serial")
        self._adb = self.spec.get("adb_path")
        d = cu_target.state_dir(cu_target.runtime_root(), env_id,
                                _safe_component(self.serial()), "default")
        self.env_dir = Path(d)

    # -- plumbing --------------------------------------------------------------

    def _adb_bin(self):
        adb = self._adb or os.environ.get("CU_ADB") \
            or shutil.which("adb")
        if not adb:
            raise BackendError("adb_not_found:install platform-tools")
        return adb

    def _default_run(self, argv, timeout_s):
        return subprocess.run([self._adb_bin(), *[str(a) for a in argv]],
                              capture_output=True, timeout=timeout_s)

    def _call(self, argv, timeout_s=15, binary=False):
        try:
            p = self._run(["-s", self.serial(), *argv], timeout_s)
        except subprocess.TimeoutExpired:
            raise BackendError(f"adb_timeout:{argv[0]}")
        except BackendError:
            raise
        except Exception as exc:
            raise BackendError(f"adb:{type(exc).__name__}:{exc}")
        if binary:
            return p.stdout
        out = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        if p.returncode != 0:
            raise BackendError(
                f"adb_rc{p.returncode}:{(err or out).strip()[:200]}")
        return out

    def serial(self):
        if self._serial:
            return self._serial
        try:
            out = self._run(["devices"], 10)
        except subprocess.TimeoutExpired:
            raise BackendError("adb_timeout:devices")
        devs = [l.split("\t")[0].strip()
                for l in out.stdout.decode("utf-8", "replace").splitlines()
                if "\tdevice" in l]
        if not devs:
            raise BackendError("no_device:adb devices lists none")
        if len(devs) > 1:
            raise BackendError(f"ambiguous_devices:{devs}:set serial")
        self._serial = devs[0]
        return self._serial

    def hint_scope(self):
        return (self.env_id, _safe_component(self.serial()), "default")

    # -- observation -----------------------------------------------------------

    def observe(self, timeout_s=15):
        """exec-out screencap -p (binary-safe, no CRLF mangling).
        Magic bytes are parse_frame's authority — garbage raises a
        typed BackendError, never a silent decode."""
        data = self._call(["exec-out", "screencap", "-p"], timeout_s,
                          binary=True)
        if not data:
            raise BackendError("screencap:empty")
        path = _png_path(self.env_dir)
        path.write_bytes(data)
        img = parse_frame(path)
        meta = {"backend": "adb", "origin_px": [0, 0],
                "size_px": [img.width, img.height],
                "frame_sha256": hashlib.sha256(img.rgb).hexdigest(),
                "instance_id": self.serial(), "env_id": self.env_id,
                "monotonic_ns": time.monotonic_ns()}
        return img, meta

    def ui_elements(self, timeout_s=20):
        """uiautomator dump -> real node tree -> hint-shape elements.
        Real devices can exit 0 yet fail ('could not get idle state' on
        animated screens) leaving no/empty XML — retry, then raise a
        typed BackendError instead of a raw ParseError."""
        remote = "/data/local/tmp/cu-ui.xml"
        xml, detail = "", ""
        for _ in range(3):
            try:
                out = self._call(["shell", "uiautomator", "dump", remote],
                                 timeout_s)
                detail = out.strip()
                xml = self._call(["exec-out", "cat", remote], timeout_s)
            except BackendError as exc:
                detail = str(exc)
            if xml.lstrip().startswith("<"):
                break
            xml = ""
            time.sleep(1)
        self._call(["shell", "rm", "-f", remote], 5)
        if not xml:
            raise BackendError(f"uia_dump:{(detail or 'no xml')[:200]}")
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            raise BackendError(f"uia_parse:{exc}")
        out = []
        for node in root.iter("node"):
            if node.get("enabled", "true") != "true":
                continue
            m = _BOUNDS_RX.match(node.get("bounds", ""))
            if not m:
                continue
            x1, y1, x2, y2 = (int(v) for v in m.groups())
            if x2 <= x1 or y2 <= y1:
                continue
            interactive = any(node.get(a) == "true"
                              for a in _CLICKABLE_ATTRS)
            name = node.get("text") or node.get("content-desc") or ""
            if not interactive and not name:
                continue
            cls = (node.get("class") or "").rsplit(".", 1)[-1]
            out.append({"x": (x1 + x2) // 2, "y": (y1 + y2) // 2,
                        "name": name or cls, "type": cls,
                        "bounds": [x1, y1, x2 - x1, y2 - y1],
                        "enabled": True, "hwnd": None})
        return out

    # -- input -----------------------------------------------------------------

    def send_events(self, events, timeout_s=15):
        """events = list of remote-shell argv (e.g. ["input","tap","5","7"]).
        Runs each via `adb shell`; a mid-batch failure raises BackendError —
        the outcome of in-flight taps is unknowable (never retried)."""
        sent = 0
        for ev in events:
            self._call(["shell", *ev], timeout_s)
            sent += 1
        return {"dispatched": sent}

    def pointer_position(self):
        raise BackendError("position_unavailable:no cursor on touch")

    # -- guest channel (adb shell IS the exec channel) --------------------------

    def guest_caps(self):
        return {"exec": True, "uia": True}

    def guest_call(self, method, params=None, timeout_s=15):
        params = params or {}
        if method == "exec.run":
            cmd = params.get("cmd", "")
            # adb joins `shell` argv with spaces — ["shell","sh","-c",cmd]
            # makes remote `sh -c` see only the first word of cmd. One argv
            # element keeps multi-word commands intact (`:` = shell no-op).
            p = self._run(["-s", self.serial(), "shell",
                           cmd or ":"], timeout_s)
            return {"ok": True,
                    "stdout": p.stdout.decode("utf-8", "replace")[:16000],
                    "stderr": p.stderr.decode("utf-8", "replace")[:4000],
                    "exit_code": p.returncode}
        if method == "uia.snapshot":
            return {"ok": True, "elements": self.ui_elements()}
        raise BackendError(f"guest:unknown_method:{method}")

    def release_all(self, timeout_s=5):
        return {"released": "adb"}   # input.* has no held modifier state

    def status(self):
        return {"device_state": self._call(["get-state"], 10).strip(),
                "serial": self.serial()}


# -- event encoders (parallel to cu_qmp_backend.encode_*) ----------------------

def encode_move(x, y, w, h):
    raise UnsupportedOp("move:no hover cursor on a touch device")


def encode_click(x, y, w, h, button="left", clicks=1):
    if button not in ("left",):
        raise UnsupportedOp(f"button:{button}:touch has only tap")
    if not (0 <= x < w and 0 <= y < h):
        raise UnsupportedOp(f"oob:{x},{y} outside {w}x{h}")
    if clicks and int(clicks) > 1:
        return [["input", "tap", x, y]] * int(clicks)
    return [["input", "tap", x, y]]


def encode_tap(x, y):
    return [["input", "tap", int(x), int(y)]]


def encode_swipe(x0, y0, x1, y1, ms=300):
    return [["input", "swipe", int(x0), int(y0), int(x1), int(y1),
             int(ms)]]


def encode_scroll(dx, dy, w, h):
    """Wheel-style scroll = a center swipe. dy>0 (content down) = swipe up."""
    evs = []
    steps = min(3, max(1, abs(dx or 0) + abs(dy or 0)))
    for _ in range(steps):
        if abs(dy or 0) >= abs(dx or 0):
            if (dy or 0) > 0:
                evs += encode_swipe(w // 2, int(h * 0.65),
                                    w // 2, int(h * 0.35))
            else:
                evs += encode_swipe(w // 2, int(h * 0.35),
                                    w // 2, int(h * 0.65))
        elif (dx or 0) > 0:
            evs += encode_swipe(int(w * 0.65), h // 2,
                                int(w * 0.35), h // 2)
        else:
            evs += encode_swipe(int(w * 0.35), h // 2,
                                int(w * 0.65), h // 2)
    return evs


def encode_drag(x0, y0, x1, y1, w, h, button="left", steps=64):
    ms = min(2000, max(150, steps * 8))
    return encode_swipe(x0, y0, x1, y1, ms)


def encode_key(name):
    code = _KEYCODES.get(str(name).lower())
    if code is None:
        raise UnsupportedOp(f"key:{name}")
    return [["input", "keyevent", code]]


def encode_chord(chord):
    raise UnsupportedOp(f"chord:{chord}:no reliable modifiers via input")


def encode_text(text, layout=None):
    return [["input", "text", _escape_input_text(text)]]
