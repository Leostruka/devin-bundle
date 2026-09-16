#!/usr/bin/env python3
"""Mouse control: move, click, scroll, drag, position. Prints JSON to stdout.

Action profiles (see profile.py / cu_motion.py): fast (teleport, default),
smooth (cinematic arc), human (bezier + jitter + Fitts timing). Resolve order:
--profile > $COMPUTER_USE_PROFILE > session file > fast.

Requires pynput (installed via requirements.txt into the extension's .venv).
"""
import argparse
import json
import random
import sys
import time

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


def _move(mouse, x, y, profile, target_w=30.0, dry_run=False):
    """Move cursor to (x, y) per profile. Returns (points, duration_s)."""
    if profile == "fast":
        if not dry_run:
            mouse.position = (x, y)
        return 1, 0.0
    cx, cy = mouse.position
    pts, dur = cm.gen_path(profile, cx, cy, x, y, target_w)
    if not dry_run:
        cm.play_path(mouse, pts, dur)
    return len(pts), dur


def _resolve_xy(args):
    """click/move may take --hint instead of x y positionals."""
    if getattr(args, "hint", None):
        hit = cu_hints.resolve_hint(args.hint)
        if not hit:
            fail(f"unknown hint {args.hint!r} — run screenshot.py --hints first")
        return hit[0], hit[1], hit[2]
    if args.x is None or args.y is None:
        fail("x and y are required unless --hint is given", 2)
    return args.x, args.y, ""


def main():
    p = cm.JsonParser(description="Mouse control via pynput")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("move", "click", "scroll", "drag"):
        sp = sub.add_parser(name)
        sp.add_argument("--profile", choices=cm.PROFILES, default=None,
                        help="action profile override for this call")
        sp.add_argument("--dry-run", action="store_true",
                        help="compute path/timing but dispatch no input")
        if name in ("move", "click"):
            sp.add_argument("x", type=int, nargs="?")
            sp.add_argument("y", type=int, nargs="?")
            sp.add_argument("--hint", default=None,
                            help="hint id from screenshot.py --hints "
                                 "(resolves to element center)")
        else:
            sp.add_argument("x", type=int)
            sp.add_argument("y", type=int)
        if name == "click":
            sp.add_argument("--button", default="left",
                            choices=["left", "right", "middle"])
            sp.add_argument("--clicks", type=int, default=1,
                            help="1=single, 2=double (default: 1)")
            sp.add_argument("--hold", type=int, default=None,
                            help="ms between press and release (default: "
                                 "profile-driven; human jitters ~70ms)")
            sp.add_argument("--target-w", type=float, default=30.0,
                            help="target width px for Fitts timing (human)")
        if name == "scroll":
            sp.add_argument("--dx", type=int, default=0, help="horizontal steps")
            sp.add_argument("--dy", type=int, default=0, help="vertical steps (+ down)")
        if name == "drag":
            sp.add_argument("--from-x", type=int, required=True)
            sp.add_argument("--from-y", type=int, required=True)
            sp.add_argument("--duration", type=float, default=None)
    spos = sub.add_parser("position", help="Print current cursor position")

    args = p.parse_args()
    set_dpi_awareness()

    try:
        from pynput.mouse import Button, Controller
    except ImportError:
        fail("pynput not installed — run: <venv-python> -m pip install -r requirements.txt", 2)

    profile = cm.get_profile(getattr(args, "profile", None))
    mouse = Controller()
    try:
        if args.cmd == "position":
            x, y = mouse.position
            print(json.dumps({"ok": True, "x": x, "y": y}))
            return
        if args.cmd == "move":
            x, y, hint_name = _resolve_xy(args)
            n, dur = _move(mouse, x, y, profile, dry_run=args.dry_run)
            fx, fy = mouse.position
            out = {"ok": True, "cmd": "move", "x": fx, "y": fy,
                   "profile": profile, "points": n, "secs": round(dur, 3)}
            if hint_name:
                out["hint"] = args.hint
            if args.dry_run:
                out["dry_run"] = True
                out["x"], out["y"] = x, y
            print(json.dumps(out))
            return
        if args.cmd == "click":
            x, y, hint_name = _resolve_xy(args)
            n, dur = _move(mouse, x, y, profile, target_w=args.target_w,
                           dry_run=args.dry_run)
            hold = cm.click_hold(profile, args.hold)
            if not args.dry_run:
                time.sleep(cm.pre_click_delay(profile))
                btn = getattr(Button, args.button)
                for i in range(args.clicks):
                    mouse.press(btn)
                    time.sleep(hold)
                    mouse.release(btn)
                    if i < args.clicks - 1:
                        time.sleep(0.08 if profile == "fast"
                                   else max(0.03, random.gauss(0.11, 0.03)))
            fx, fy = mouse.position
            out = {"ok": True, "cmd": "click", "x": fx, "y": fy,
                   "profile": profile, "points": n, "secs": round(dur, 3)}
            if hint_name:
                out["hint"] = args.hint
                out["hint_name"] = hint_name
            if args.dry_run:
                out["dry_run"] = True
                out["x"], out["y"] = x, y
            print(json.dumps(out))
            return
        if args.cmd == "scroll":
            if profile == "fast":
                if not args.dry_run:
                    mouse.position = (args.x, args.y)
                    time.sleep(0.05)
                    mouse.scroll(args.dx, args.dy)
            else:
                _move(mouse, args.x, args.y, profile, dry_run=args.dry_run)
                if not args.dry_run:
                    seq = ([(1 if args.dx > 0 else -1, 0)] * abs(args.dx)
                           + [(0, 1 if args.dy > 0 else -1)] * abs(args.dy))
                    for (sx, sy), gap in zip(seq, cm.scroll_gaps(profile, len(seq))):
                        mouse.scroll(sx, sy)
                        time.sleep(gap)
            fx, fy = mouse.position
            out = {"ok": True, "cmd": "scroll", "x": fx, "y": fy,
                   "profile": profile}
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
        if args.cmd == "drag":
            dur = args.duration
            if dur is None:
                dur = 0.3 if profile == "fast" else (0.6 if profile == "smooth" else 0.8)
            if not args.dry_run:
                if profile == "fast":
                    mouse.position = (args.from_x, args.from_y)
                    time.sleep(0.05)
                    mouse.press(Button.left)
                    steps = max(int(dur / 0.02), 1)
                    for i in range(1, steps + 1):
                        t = i / steps
                        mouse.position = (
                            round(args.from_x + (args.x - args.from_x) * t),
                            round(args.from_y + (args.y - args.from_y) * t))
                        time.sleep(dur / steps)
                    mouse.release(Button.left)
                else:
                    mouse.position = (args.from_x, args.from_y)
                    time.sleep(cm.pre_click_delay(profile))
                    mouse.press(Button.left)
                    pts, _ = cm.gen_path(profile, args.from_x, args.from_y,
                                         args.x, args.y)
                    cm.play_path(mouse, pts, dur)
                    mouse.release(Button.left)
            fx, fy = mouse.position
            out = {"ok": True, "cmd": "drag", "x": fx, "y": fy,
                   "profile": profile}
            if args.dry_run:
                out["dry_run"] = True
            print(json.dumps(out))
            return
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
