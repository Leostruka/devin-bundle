#!/usr/bin/env python3
"""P7 probe: numpy FFT-NCC template matching (no cv2).

Fixture: p1_target --drawtext window -> mss grab -> crop template at a
known position -> search in the full 1920x1080 shot.

Measures:
  match_ms      FFT-NCC vs direct spatial NCC (scipy-free)
  precision     argmax vs ground-truth offset (px)
  robustness    +gaussian noise, +/-10% template scale
  scoped        same match inside a 640x480 region (daemon-realistic)
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_deps"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..",
                                  "extensions", "computer-use"))

import numpy as np  # noqa: E402
import mss  # noqa: E402

TRIALS = int(sys.argv[sys.argv.index("--trials") + 1]) \
    if "--trials" in sys.argv else 10

user32 = ctypes.windll.user32


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


def gray(img):
    return img[:, :, 2] * 0.299 + img[:, :, 1] * 0.587 + img[:, :, 0] * 0.114


def ncc_fft(img, tpl):
    """Normalized cross-correlation via FFT + integral-image local stats.

    Returns score map for top-left positions (valid region)."""
    ih, iw = img.shape
    th, tw = tpl.shape
    t = tpl - tpl.mean()
    # cross-correlation numerator
    fs = (ih + th - 1, iw + tw - 1)
    corr = np.fft.irfft2(np.fft.rfft2(img, fs) *
                         np.fft.rfft2(t[::-1, ::-1], fs), fs)
    corr = corr[th - 1:ih, tw - 1:iw]
    # local mean/std via integral image
    ii = np.zeros((ih + 1, iw + 1))
    ii[1:, 1:] = img.cumsum(0).cumsum(1)
    ii2 = np.zeros((ih + 1, iw + 1))
    ii2[1:, 1:] = (img * img).cumsum(0).cumsum(1)

    def box_sum(m):
        return (m[th:, tw:] - m[:-th, tw:] - m[th:, :-tw] + m[:-th, :-tw])

    n = th * tw
    s = box_sum(ii) / n
    ss = box_sum(ii2) / n - s * s
    den = np.sqrt(n * np.clip(ss, 0, None)) * np.sqrt((t * t).sum())
    return corr / np.where(den > 0, den, 1)


def ncc_direct(img, tpl):
    """Sliding-window NCC via strided views — reference impl."""
    ih, iw = img.shape
    th, tw = tpl.shape
    t = tpl - tpl.mean()
    tden = np.sqrt((t * t).sum())
    from numpy.lib.stride_tricks import sliding_window_view
    win = sliding_window_view(img, (th, tw))  # (H, W, th, tw)
    wm = win.mean(axis=(2, 3), keepdims=True)
    wc = win - wm
    num = (wc * t).sum(axis=(2, 3))
    den = np.sqrt((wc * wc).sum(axis=(2, 3))) * tden
    return num / np.where(den > 0, den, 1)


def argmax2(m):
    i = int(np.argmax(m))
    return divmod(i, m.shape[1]), float(m.flat[i])


def summ(v):
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "p50": round(statistics.median(v), 3),
            "p95": round(s[min(len(s) - 1, int(len(s) * 0.95))], 3)}


def main():
    rep = {"ok": True}
    marker = f"cu_p7_{int(time.time())}"
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "p1_target.py"),
         marker, "90", "--drawtext", "--topmost"])
    hwnd = find_window(marker)
    if not hwnd:
        print(json.dumps({"ok": False}))
        return
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    time.sleep(0.3)

    sct = mss.MSS()
    mon = {"left": 0, "top": 0, "width": 1920, "height": 1080}
    shot = np.array(sct.grab(mon))  # BGRA
    g = gray(shot).astype(np.float64)

    # ground truth: template = text area inside window (drawtext paints
    # text near top-left of client area, ~ (x+30,y+60) in window coords)
    tx, ty = r.left + 30, r.top + 60
    TH, TW = 60, 120
    tpl = g[ty:ty + TH, tx:tx + TW].copy()
    rep["tpl"] = {"x": tx, "y": ty, "w": TW, "h": TH,
                  "std": round(float(tpl.std()), 1)}

    # full-screen FFT-NCC
    ms_fft, hits_fft = [], []
    for _ in range(TRIALS):
        t0 = time.perf_counter()
        m = ncc_fft(g, tpl)
        (yy, xx), sc = argmax2(m)
        ms_fft.append((time.perf_counter() - t0) * 1000)
        hits_fft.append(abs(xx - tx) <= 1 and abs(yy - ty) <= 1)
    rep["fft_full_ms"] = summ(ms_fft)
    rep["fft_hit"] = f"{sum(hits_fft)}/{TRIALS}"
    rep["fft_score"] = round(sc, 3)

    # scoped region (640x480 around window) — daemon-realistic
    rx, ry = r.left - 20, r.top - 20
    reg = g[ry:ry + 480, rx:rx + 640]
    ms_reg, hits_reg = [], []
    for _ in range(TRIALS):
        t0 = time.perf_counter()
        m = ncc_fft(reg, tpl)
        (yy, xx), sc = argmax2(m)
        ms_reg.append((time.perf_counter() - t0) * 1000)
        hits_reg.append(abs(xx - (tx - rx)) <= 1 and abs(yy - (ty - ry)) <= 1)
    rep["fft_region_ms"] = summ(ms_reg)
    rep["fft_region_hit"] = f"{sum(hits_reg)}/{TRIALS}"

    # direct NCC on region (reference timing)
    ms_dir = []
    for _ in range(min(TRIALS, 3)):
        t0 = time.perf_counter()
        m = ncc_direct(reg, tpl)
        argmax2(m)
        ms_dir.append((time.perf_counter() - t0) * 1000)
    rep["direct_region_ms"] = summ(ms_dir)

    # noise robustness: sigma=12 gaussian
    rng = np.random.default_rng(7)
    gn = np.clip(g + rng.normal(0, 12, g.shape), 0, 255)
    m = ncc_fft(gn, tpl)
    (yy, xx), sc = argmax2(m)
    rep["noise_hit"] = abs(xx - tx) <= 1 and abs(yy - ty) <= 1
    rep["noise_score"] = round(sc, 3)

    # scale robustness: template resized 110% / 90% (nearest)
    for f in (1.1, 0.9):
        th2, tw2 = int(TH * f), int(TW * f)
        ys = (np.arange(th2) / f).astype(int)
        xs = (np.arange(tw2) / f).astype(int)
        t2 = tpl[np.ix_(ys, xs)]
        m = ncc_fft(reg, t2)
        (yy, xx), sc = argmax2(m)
        rep[f"scale_{f}_hit"] = abs(xx - (tx - rx)) <= 2
        rep[f"scale_{f}_score"] = round(sc, 3)

    print(json.dumps(rep, indent=1))
    proc.kill()


if __name__ == "__main__":
    main()
