#!/usr/bin/env python3
"""Mouse control: move, click, scroll, drag, position. Prints JSON to stdout.

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


def main():
    p = argparse.ArgumentParser(description="Mouse control via pynput")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("move", "click", "scroll", "drag"):
        sp = sub.add_parser(name)
        sp.add_argument("x", type=int)
        sp.add_argument("y", type=int)
        if name == "click":
            sp.add_argument("--button", default="left",
                            choices=["left", "right", "middle"])
            sp.add_argument("--clicks", type=int, default=1,
                            help="1=single, 2=double (default: 1)")
            sp.add_argument("--hold", type=int, default=50,
                            help="ms between press and release (default: 50; "
                                 "raise for UIs that ignore instant clicks)")
        if name == "scroll":
            sp.add_argument("--dx", type=int, default=0, help="horizontal steps")
            sp.add_argument("--dy", type=int, default=0, help="vertical steps (+ down)")
        if name == "drag":
            sp.add_argument("--from-x", type=int, required=True)
            sp.add_argument("--from-y", type=int, required=True)
            sp.add_argument("--duration", type=float, default=0.3)
    sub.add_parser("position", help="Print current cursor position")

    args = p.parse_args()
    set_dpi_awareness()

    try:
        from pynput.mouse import Button, Controller
    except ImportError:
        fail("pynput not installed — run: <venv-python> -m pip install -r requirements.txt", 2)

    mouse = Controller()
    try:
        if args.cmd == "position":
            x, y = mouse.position
            print(json.dumps({"ok": True, "x": x, "y": y}))
            return
        if args.cmd == "move":
            mouse.position = (args.x, args.y)
        elif args.cmd == "click":
            mouse.position = (args.x, args.y)
            time.sleep(0.05)
            btn = getattr(Button, args.button)
            for i in range(args.clicks):
                mouse.press(btn)
                time.sleep(max(args.hold, 0) / 1000)
                mouse.release(btn)
                if i < args.clicks - 1:
                    time.sleep(0.08)
        elif args.cmd == "scroll":
            mouse.position = (args.x, args.y)
            time.sleep(0.05)
            mouse.scroll(args.dx, args.dy)
        elif args.cmd == "drag":
            mouse.position = (args.from_x, args.from_y)
            time.sleep(0.05)
            mouse.press(Button.left)
            steps = max(int(args.duration / 0.02), 1)
            for i in range(1, steps + 1):
                t = i / steps
                mouse.position = (round(args.from_x + (args.x - args.from_x) * t),
                                  round(args.from_y + (args.y - args.from_y) * t))
                time.sleep(args.duration / steps)
            mouse.release(Button.left)
        x, y = mouse.position
        print(json.dumps({"ok": True, "cmd": args.cmd, "x": x, "y": y}))
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
