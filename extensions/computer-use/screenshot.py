#!/usr/bin/env python3
"""Capture the screen to a PNG file. Prints a JSON result to stdout.

Requires mss (installed via requirements.txt into the extension's .venv).
"""
import argparse
import json
import os
import sys
import tempfile
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


def _save_with_grid(img, spacing, out):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        fail("pillow required for --grid — run: "
             "<venv-python> -m pip install -r requirements.txt", 2)
    if spacing < 20:
        fail("--grid spacing must be >= 20 px", 2)
    im = Image.frombytes("RGB", (img.width, img.height), img.rgb).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    try:
        font = ImageFont.load_default(size=18)
    except TypeError:
        font = ImageFont.load_default()
    line = (255, 255, 0, 110)
    for x in range(0, img.width, spacing):
        d.line([(x, 0), (x, img.height)], fill=line)
        d.text((x + 2, 2), str(x), font=font, fill=(255, 255, 0, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for y in range(0, img.height, spacing):
        d.line([(0, y), (img.width, y)], fill=line)
        d.text((2, y + 2), str(y), font=font, fill=(255, 255, 0, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 255))
    Image.alpha_composite(im, ov).convert("RGB").save(out, "PNG")


def main():
    p = argparse.ArgumentParser(description="Capture screen to PNG")
    p.add_argument("--out", default=None,
                   help="Output PNG path (default: screenshot-<ts>.png in the "
                        "system temp dir; use a .devin/ path to keep it as "
                        "project documentation)")
    p.add_argument("--monitor", type=int, default=0,
                   help="Monitor index: 0 = all monitors combined (default), 1..N = specific")
    p.add_argument("--region", default=None,
                   help="Crop region as 'x,y,w,h' (pixels)")
    p.add_argument("--grid", type=int, nargs="?", const=100, default=None,
                   metavar="PX",
                   help="Overlay a coordinate grid with physical-pixel labels "
                        "every PX px (default 100). Use when picking click "
                        "targets — the labels survive image rescaling.")
    args = p.parse_args()

    set_dpi_awareness()
    out = args.out or os.path.join(tempfile.gettempdir(),
                                   f"screenshot-{int(time.time())}.png")

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
            if args.grid:
                _save_with_grid(img, args.grid, out)
            else:
                mss.tools.to_png(img.rgb, img.size, output=out)
        result = {"ok": True, "path": out, "width": img.width,
                  "height": img.height, "monitor": args.monitor}
        if args.grid:
            result["grid_px"] = args.grid
            result["note"] = "grid labels are physical pixels — read click coords directly"
        print(json.dumps(result))
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
