#!/usr/bin/env python3
"""Keyboard control: type literal text, press a key, or fire a hotkey chord.
Prints JSON to stdout.

Action profiles (see profile.py / cu_motion.py): fast (instant, default),
smooth (fixed 35ms/char), human (lognormal digram/trigram-context cadence —
repeated letters faster, punctuation pauses; seedable via --seed/$CU_SEED).
An explicit --delay always wins.

Requires pynput (installed via requirements.txt into the extension's .venv).
"""
import argparse
import json
import random
import sys
import time

import cu_actions
import cu_motion as cm
import cu_hints


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
    p.add_argument("--hint", default=None,
                   help="hint id from screenshot.py --hints; targets the "
                        "element instead of the focused window")
    p.add_argument("--via", default="auto",
                   choices=["auto", "physical", "uia"],
                   help="with --hint: auto uses the element's UIA Value "
                        "pattern when available, falling back to physical "
                        "typing; 'uia' rejects instead of falling back")
    p.add_argument("--seed", type=int, default=None,
                   help="seed the human-typing RNG (or set $CU_SEED) for a "
                        "reproducible cadence")
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
            t0 = cu_actions.now_ms()
            if not args.dry_run:
                with cu_actions.OwnedInputs() as owned:
                    for k in keys:
                        owned.press(kb, k)
                        g = cm.key_gap(profile)
                        if g:
                            time.sleep(g)
                    for k in reversed(keys):
                        owned.release(kb, k)
            out = cu_actions.result(
                "dispatched", "physical", keys=args.keys, profile=profile,
                timings_ms={"move": None, "dispatch": None,
                            "total": round(cu_actions.now_ms() - t0, 1)})
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
        if args.key:
            k = resolve_key(args.key, Key, KeyCode)
            t0 = cu_actions.now_ms()
            if not args.dry_run:
                with cu_actions.OwnedInputs() as owned:
                    owned.press(kb, k)
                    g = cm.key_gap(profile)
                    if g:
                        time.sleep(g)
                    owned.release(kb, k)
            out = cu_actions.result(
                "dispatched", "physical", key=args.key, profile=profile,
                timings_ms={"move": None, "dispatch": None,
                            "total": round(cu_actions.now_ms() - t0, 1)})
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
        if args.text is not None:
            entry = None
            if args.hint:
                entry, reason = cu_hints.resolve_hint(args.hint)
                if not entry:
                    fail(f"hint {args.hint!r} rejected: {reason} — "
                         "rerun screenshot.py --hints")
            t0 = cu_actions.now_ms()
            backend = "physical"
            uia_note = None
            if entry is not None and args.via != "physical" \
                    and not args.dry_run:
                res, reason = cu_hints.uia_perform(entry, "set_value",
                                                   args.text)
                if res:
                    backend = "uia"
                elif args.via == "uia":
                    fail(f"uia set_value rejected: {reason}")
                else:
                    uia_note = reason
            delays = cm.type_delays(
                args.text, profile,
                args.delay if args.delay > 0 else None, seed=args.seed)
            if not args.dry_run and backend == "physical":
                if delays is None:
                    kb.type(args.text)
                else:
                    for ch, d in zip(args.text, delays):
                        kb.type(ch)
                        time.sleep(d)
                if args.enter:
                    if profile == "human":
                        time.sleep(max(0.02, random.gauss(0.15, 0.05)))
                    with cu_actions.OwnedInputs() as owned:
                        owned.press(kb, Key.enter)
                        owned.release(kb, Key.enter)
            out = cu_actions.result(
                "dispatched", backend, typed=len(args.text),
                profile=profile,
                delay_mode=("uia" if backend == "uia" else
                            "instant" if delays is None else
                            "fixed" if args.delay > 0 else profile),
                timings_ms={"move": None, "dispatch": None,
                            "total": round(cu_actions.now_ms() - t0, 1)})
            if entry is not None:
                out["hint"] = args.hint
            if uia_note:
                out["dispatch"]["uia_fallback"] = uia_note
            if delays and backend == "physical":
                out["secs"] = round(sum(delays), 3)  # planned cadence
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
