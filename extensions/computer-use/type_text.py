#!/usr/bin/env python3
"""Keyboard control: type literal text, press a key, or fire a hotkey chord.
Prints JSON to stdout.

Requires pynput (installed via requirements.txt into the extension's .venv).
"""
import argparse
import json
import sys
import time


def set_dpi_awareness():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


KEY_ALIASES = {
    "ctrl": "ctrl", "control": "ctrl", "alt": "alt", "shift": "shift",
    "win": "cmd", "cmd": "cmd", "super": "cmd", "meta": "cmd",
    "enter": "enter", "return": "enter", "esc": "esc", "escape": "esc",
    "tab": "tab", "space": "space", "backspace": "backspace",
    "delete": "delete", "del": "delete", "insert": "insert",
    "home": "home", "end": "end", "pageup": "page_up", "pagedown": "page_down",
    "up": "up", "down": "down", "left": "left", "right": "right",
    "capslock": "caps_lock", "numlock": "num_lock", "printscreen": "print_screen",
}
for i in range(1, 25):
    KEY_ALIASES[f"f{i}"] = f"f{i}"


def resolve_key(name, Key, KeyCode):
    n = name.strip().lower()
    n = KEY_ALIASES.get(n, n)
    if hasattr(Key, n):
        return getattr(Key, n)
    if len(name.strip()) == 1:
        return KeyCode.from_char(name.strip())
    fail(f"unknown key: {name}", 2)


def main():
    p = argparse.ArgumentParser(description="Keyboard control via pynput")
    p.add_argument("text", nargs="?", default=None, help="Literal text to type")
    p.add_argument("--key", default=None, help="Single key name (e.g. enter, tab, f5)")
    p.add_argument("--keys", default=None,
                   help="Hotkey chord, '+'-separated (e.g. 'ctrl+c', 'ctrl+shift+s')")
    p.add_argument("--delay", type=float, default=0.0,
                   help="Delay between keystrokes in seconds (default: 0)")
    p.add_argument("--enter", action="store_true",
                   help="Press Enter after typing the literal text")
    args = p.parse_args()

    if not any([args.text, args.key, args.keys]):
        p.error("provide text, --key, or --keys")

    set_dpi_awareness()
    try:
        from pynput.keyboard import Controller, Key, KeyCode
    except ImportError:
        fail("pynput not installed — run: <venv-python> -m pip install -r requirements.txt", 2)

    kb = Controller()
    try:
        if args.keys:
            keys = [resolve_key(k, Key, KeyCode) for k in args.keys.split("+")]
            for k in keys:
                kb.press(k)
            for k in reversed(keys):
                kb.release(k)
            print(json.dumps({"ok": True, "keys": args.keys}))
            return
        if args.key:
            k = resolve_key(args.key, Key, KeyCode)
            kb.press(k)
            kb.release(k)
            print(json.dumps({"ok": True, "key": args.key}))
            return
        if args.text is not None:
            if args.delay > 0:
                for ch in args.text:
                    kb.type(ch)
                    time.sleep(args.delay)
            else:
                kb.type(args.text)
            if args.enter:
                kb.press(Key.enter)
                kb.release(Key.enter)
            print(json.dumps({"ok": True, "typed": len(args.text)}))
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
