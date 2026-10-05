"""cu_ocr.py — WinRT OCR text -> screen coordinates on any raster surface.

    cu_ocr.py find "Submit" --window 123456     # word rects for matches
    cu_ocr.py find "OK" --region 100,100,800,600
    cu_ocr.py all --window 123456               # every word in the surface

Windows.Media.Ocr returns word bounding_rects in image space; this CLI
adds the capture origin so results land in physical screen coordinates
(same space as mouse.py / UIA hints).

Measured constraints (phase-2 probe):
  - ~48px image-height floor — below it recognize_async returns EMPTY
    with no error, so small regions are upscaled before OCR.
  - First recognize call costs ~48ms (decoder warmup), steady ~8ms.
  - MaxImageDimension is runtime-queried (10000 on the probe host);
    oversized inputs are downscaled like cu_terminal._ocr_image.
  - OCR is noisy at word level ("OK" -> "0k"); callers should prefer
    multi-char queries and use --all for full context.
"""
import argparse
import asyncio
import json
import os
import sys
import tempfile

import cu_dpi
import cu_target

_MIN_OCR_HEIGHT = 96      # below ~48px the engine returns empty silently
_UPSCALE = 4


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def _grab_region(region):
    """mss grab of (x, y, w, h) -> PIL image, or None."""
    x, y, w, h = region
    if w < 8 or h < 8:
        return None
    try:
        import mss
        from PIL import Image
    except ImportError:
        return None
    with mss.MSS() as sct:
        shot = sct.grab({"left": x, "top": y, "width": w, "height": h})
        return Image.frombytes("RGBA", shot.size, shot.bgra, "raw", "BGRA")


def _upscaled(img):
    """Small images get nearest-neighbor upscale for the 48px floor;
    returns (image, scale_applied)."""
    if img.height >= _MIN_OCR_HEIGHT:
        return img, 1.0
    s = max(_UPSCALE, -(-_MIN_OCR_HEIGHT // img.height))
    return img.resize((img.width * s, img.height * s),
                      resample=0), float(s)


def _ocr_words(png_path):
    """Windows.Media.Ocr -> [(word, x, y, w, h)] in IMAGE space, or
    None when winrt/engine unavailable."""
    try:
        import winrt.windows.storage.streams  # noqa: F401
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.storage import StorageFile, FileAccessMode
        from winrt.windows.graphics.imaging import (
            BitmapDecoder, BitmapTransform)
        import winrt.windows.foundation.collections  # noqa: F401
    except Exception:
        return None

    async def _go():
        f = await StorageFile.get_file_from_path_async(
            os.path.abspath(png_path))
        s = await f.open_async(FileAccessMode.READ)
        try:
            dec = await BitmapDecoder.create_async(s)
            eng = OcrEngine.try_create_from_user_profile_languages()
            if eng is None:
                return None
            maxd = OcrEngine.max_image_dimension
            w, h = dec.oriented_pixel_width, dec.oriented_pixel_height
            if max(w, h) > maxd:
                scale = maxd / max(w, h)
                tr = BitmapTransform()
                tr.scaled_width = int(w * scale)
                tr.scaled_height = int(h * scale)
                bmp = await dec.get_software_bitmap_async(
                    dec.bitmap_pixel_format, dec.bitmap_alpha_mode, tr,
                    0, 0)
            else:
                bmp = await dec.get_software_bitmap_async()
            res = await eng.recognize_async(bmp)
            out = []
            for line in res.lines:
                for word in line.words:
                    r = word.bounding_rect
                    out.append((word.text, r.x, r.y, r.width, r.height))
            return out
        finally:
            s.close()

    try:
        return asyncio.run(_go())
    except Exception:
        return None


def find_words(region, query=None):
    """Grab + OCR + map to screen coords. Returns (matches, meta) or
    None on capture/OCR failure."""
    img = _grab_region(region)
    if img is None:
        return None
    img, scale = _upscaled(img)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        img.save(path, format="PNG")
        words = _ocr_words(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if words is None:
        return None
    ox, oy = region[0], region[1]
    out = []
    for text, x, y, w, h in words:
        sx, sy = x / scale + ox, y / scale + oy
        out.append({"text": text, "x": round(sx, 1), "y": round(sy, 1),
                    "w": round(w / scale, 1), "h": round(h / scale, 1),
                    "cx": round(sx + w / scale / 2, 1),
                    "cy": round(sy + h / scale / 2, 1)})
    meta = {"upscale": scale, "engine": "winrt"}
    if query:
        ql = query.lower()
        out = [m for m in out if ql in m["text"].lower()]
    return out, meta


def _parse_region(s):
    try:
        x, y, w, h = [int(v) for v in s.split(",")]
    except ValueError:
        fail("--region must be 'x,y,w,h'")
    return (x, y, w, h)


def main():
    p = argparse.ArgumentParser(prog="cu_ocr.py")
    p.add_argument("cmd", choices=["find", "all"],
                   help="find: match query words; all: dump every word")
    p.add_argument("query", nargs="?", default=None)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--region", default=None, help="'x,y,w,h' pixels")
    src.add_argument("--window", type=int, default=None,
                     help="hwnd to capture via DWM bounds")
    args = p.parse_args()

    cu_dpi.set_dpi_awareness()
    cu_target.cli_guard(sys.argv[1:])

    if args.region:
        region = _parse_region(args.region)
    else:
        try:
            l, t, r, b = cu_dpi.physical_window_bounds(args.window)
        except OSError:
            fail(f"no_rect:{args.window}")
        region = (l, t, r - l, b - t)

    res = find_words(region, args.query if args.cmd == "find" else None)
    if res is None:
        fail("ocr unavailable (capture/winrt engine failed)")
    matches, meta = res
    print(json.dumps({"ok": True, "region": list(region),
                      "count": len(matches), "matches": matches, **meta}))


if __name__ == "__main__":
    main()
