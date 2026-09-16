#!/usr/bin/env python3
"""Capture the screen to a PNG file. Prints a JSON result to stdout.

Requires mss (installed via requirements.txt into the extension's .venv).
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
    p = argparse.ArgumentParser(description="Capture screen to PNG")
    p.add_argument("--out", default=None,
                   help="Output PNG path (default: screenshot-<ts>.png in cwd)")
    p.add_argument("--monitor", type=int, default=0,
                   help="Monitor index: 0 = all monitors combined (default), 1..N = specific")
    p.add_argument("--region", default=None,
                   help="Crop region as 'x,y,w,h' (pixels)")
    args = p.parse_args()

    set_dpi_awareness()
    out = args.out or f"screenshot-{int(time.time())}.png"

    try:
        import mss
        import mss.tools
    except ImportError:
        fail("mss not installed — run: <venv-python> -m pip install -r requirements.txt", 2)

    try:
        with mss.MSS() as sct:
            if args.region:
                try:
                    x, y, w, h = [int(v) for v in args.region.split(",")]
                except ValueError:
                    fail("--region must be 'x,y,w,h' integers", 2)
                bbox = {"left": x, "top": y, "width": w, "height": h}
            else:
                if args.monitor < 0 or args.monitor >= len(sct.monitors):
                    fail(f"monitor {args.monitor} out of range (0..{len(sct.monitors)-1})", 2)
                bbox = sct.monitors[args.monitor]
            img = sct.grab(bbox)
            mss.tools.to_png(img.rgb, img.size, output=out)
        print(json.dumps({"ok": True, "path": out, "width": img.width,
                          "height": img.height, "monitor": args.monitor}))
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
