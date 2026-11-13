#!/usr/bin/env python3
"""P4 probe: Windows.Media.Ocr as general text->coords channel.

Captures the p1_target --drawtext window via mss, runs OcrEngine, maps
word BoundingRect (image space) + region origin -> screen coords.
Verifies coordinate fidelity by re-cropping at each found word rect and
re-OCRing the crop: the same word must come back (self-contained hit
rate, no external truth needed).

Metrics: ocr_ms per full-window recognize (N runs), word hit rate,
re-crop verification rate, MaxImageDimension, engine cold-start.
Extension venv only (mss, pillow, winrt).
"""
import asyncio
import ctypes
import ctypes.wintypes as wt
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TRIALS = int(sys.argv[sys.argv.index("--trials") + 1]) \
    if "--trials" in sys.argv else 10

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
DWMWA_EXTENDED_FRAME_BOUNDS = 9


def find_window(substr, timeout=15):
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def en(h, l):
        if user32.IsWindowVisible(h):
            n = user32.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(h, b, n + 1)
                out.append((h, b.value))
        return True

    dl = time.time() + timeout
    while time.time() < dl:
        out.clear()
        user32.EnumWindows(en, 0)
        for h, t in out:
            if substr in t:
                return h
        time.sleep(0.1)
    return None


def dwm_frame(hwnd):
    r = wt.RECT()
    if dwmapi.DwmGetWindowAttribute(
            hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(r),
            ctypes.sizeof(r)) == 0:
        return (r.left, r.top, r.right, r.bottom)
    return None


_eng = None


def _engine():
    global _eng
    if _eng is None:
        from winrt.windows.media.ocr import OcrEngine
        _eng = OcrEngine.try_create_from_user_profile_languages()
    return _eng


def ocr_path(path):
    """Words+rects on a PNG, or raises. Returns (text, [(word,(x,y,w,h))])."""
    import winrt.windows.storage.streams  # noqa: F401
    import winrt.windows.foundation.collections  # noqa: F401
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage import StorageFile, FileAccessMode
    from winrt.windows.graphics.imaging import BitmapDecoder

    async def _go():
        f = await StorageFile.get_file_from_path_async(
            os.path.abspath(path))
        s = await f.open_async(FileAccessMode.READ)
        try:
            dec = await BitmapDecoder.create_async(s)
            eng = _engine()
            bmp = await dec.get_software_bitmap_async()
            res = await eng.recognize_async(bmp)
            words = []
            for line in res.lines:
                for w in line.words:
                    r = w.bounding_rect
                    words.append((w.text, (r.x, r.y, r.width, r.height)))
            return res.text, words
        finally:
            s.close()

    return asyncio.run(_go())


def grab_png(rect, out_path):
    import mss
    from PIL import Image
    l, t, r, b = rect
    with mss.mss() as sct:
        img = sct.grab({"left": l, "top": t,
                        "width": r - l, "height": b - t})
        Image.frombytes("RGB", img.size, img.rgb).save(out_path)


def crop_png(src, rect, out_path, scale=3):
    from PIL import Image
    im = Image.open(src)
    x, y, w, h = rect
    c = im.crop((int(x), int(y), int(x + w), int(y + h)))
    if scale != 1:
        c = c.resize((int(c.width * scale), int(c.height * scale)),
                     Image.NEAREST)
    c.save(out_path)


def main():
    marker = f"cu_p4_{int(time.time())}"
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "p1_target.py"),
         marker, "90", "--drawtext"])
    hwnd = find_window(marker)
    if not hwnd:
        print(json.dumps({"ok": False, "error": "no target"}))
        proc.kill()
        return
    time.sleep(0.8)  # paint settle
    rect = dwm_frame(hwnd)
    rep = {"ok": True, "window_rect": rect}

    tmp = tempfile.mkdtemp(prefix="cu_p4_")
    shot = os.path.join(tmp, "shot.png")
    grab_png(rect, shot)

    # engine cold start
    t0 = time.perf_counter()
    _engine()
    rep["engine_cold_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    from winrt.windows.media.ocr import OcrEngine
    rep["max_image_dimension"] = OcrEngine.max_image_dimension

    # timed recognize runs on the same capture
    ocr_ms = []
    words = []
    text = ""
    for i in range(TRIALS):
        t0 = time.perf_counter()
        text, words = ocr_path(shot)
        ocr_ms.append((time.perf_counter() - t0) * 1000)
        time.sleep(0.05)

    expected = {"file", "edit", "view", "help", "quick", "brown", "fox",
                "12345", "cu-perception", "ocr", "probe", "apply",
                "cancel", "ok"}
    got = {w[0].lower().strip(".,;:!?") for w in words}
    rep["words_found"] = sorted(got)
    rep["expected_hit_rate"] = round(
        len(got & expected) / len(expected), 3)
    rep["word_count"] = len(words)

    # re-crop verification: crop the word's full-width line band (word's
    # y band +- margin), 3x upscale, re-OCR — same word must return at
    # ~3x its original x (band is full-width so x scales, y inside band).
    # Word-only crops are below the engine's ~48px floor and return empty.
    from PIL import Image
    img_w = Image.open(shot).width
    verify_ok = verify_n = 0
    for word, (x, y, w, h) in words[:12]:
        if len(word) < 3 or w < 8:
            continue
        cp = os.path.join(tmp, f"c{verify_n}.png")
        crop_png(shot, (0, max(0, y - 4), img_w, h + 8), cp)
        try:
            t2, w2 = ocr_path(cp)
        except Exception:
            continue
        verify_n += 1
        for t3, r3 in w2:
            if t3.strip(".,;:!?").lower() == word.lower():
                # re-found; x' should be ~3*old_x (scale) within 20%
                if abs(r3[0] - x * 3) <= x * 3 * 0.2 + 10:
                    verify_ok += 1
                break
    rep["recrop_verify"] = {"n": verify_n, "ok": verify_ok}

    def summ(v):
        s = sorted(v)
        return {"n": len(v), "p50": round(statistics.median(v), 2),
                "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 2),
                "min": round(min(v), 2), "max": round(max(v), 2)}

    rep["ocr_ms"] = summ(ocr_ms)
    # first call includes decoder/stream warm-up — report separately
    rep["ocr_ms_first"] = round(ocr_ms[0], 2) if ocr_ms else None
    print(json.dumps(rep, indent=1))
    proc.kill()


if __name__ == "__main__":
    main()
