#!/usr/bin/env python3
"""Keyboard control: type literal text, press a key, or fire a hotkey chord.
Prints JSON to stdout.

Action profiles (see profile.py / cu_motion.py): fast (instant, default),
smooth (fixed 35ms/char), human (stochastic per-char delays ~90ms ±30ms,
double-letter speedup, rare thinking pauses). An explicit --delay always wins.

Requires pynput (installed via requirements.txt into the extension's .venv).
"""
import argparse
import json
import random
import sys
import time

import cu_motion as cm


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
    p = cm.JsonParser(description="Keyboard control via pynput")
    p.add_argument("text", nargs="?", default=None, help="Literal text to type")
    p.add_argument("--key", default=None, help="Single key name (e.g. enter, tab, f5)")
    p.add_argument("--keys", default=None,
                   help="Hotkey chord, '+'-separated (e.g. 'ctrl+c', 'ctrl+shift+s')")
    p.add_argument("--delay", type=float, default=0.0,
                   help="Fixed delay between keystrokes in seconds (overrides profile)")
    p.add_argument("--enter", action="store_true",
                   help="Press Enter after typing the literal text")
    p.add_argument("--profile", choices=cm.PROFILES, default=None,
                   help="action profile override for this call")
    p.add_argument("--dry-run", action="store_true",
                   help="compute timing plan but dispatch no input")
    args = p.parse_args()

    if not any([args.text, args.key, args.keys]):
        fail("provide text, --key, or --keys", 2)

    set_dpi_awareness()
    try:
        from pynput.keyboard import Controller, Key, KeyCode
    except ImportError:
        fail("pynput not installed — run: <venv-python> -m pip install -r requirements.txt", 2)

    profile = cm.get_profile(args.profile)
    kb = Controller()
    try:
        if args.keys:
            keys = [resolve_key(k, Key, KeyCode) for k in args.keys.split("+")]
            if not args.dry_run:
                for k in keys:
                    kb.press(k)
                    g = cm.key_gap(profile)
                    if g:
                        time.sleep(g)
                for k in reversed(keys):
                    kb.release(k)
            out = {"ok": True, "keys": args.keys, "profile": profile}
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
        if args.key:
            k = resolve_key(args.key, Key, KeyCode)
            if not args.dry_run:
                kb.press(k)
                g = cm.key_gap(profile)
                if g:
                    time.sleep(g)
                kb.release(k)
            out = {"ok": True, "key": args.key, "profile": profile}
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
        if args.text is not None:
            delays = cm.type_delays(args.text, profile,
                                    args.delay if args.delay > 0 else None)
            if not args.dry_run:
                if delays is None:
                    kb.type(args.text)
                else:
                    for ch, d in zip(args.text, delays):
                        kb.type(ch)
                        time.sleep(d)
                if args.enter:
                    if profile == "human":
                        time.sleep(max(0.02, random.gauss(0.15, 0.05)))
                    kb.press(Key.enter)
                    kb.release(Key.enter)
            out = {"ok": True, "typed": len(args.text), "profile": profile,
                   "delay_mode": ("instant" if delays is None else
                                  "fixed" if args.delay > 0 else profile)}
            if delays:
                out["secs"] = round(sum(delays), 3)
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
