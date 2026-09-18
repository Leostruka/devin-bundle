"""Pixel Sort — sort runs of pixels past a luminance threshold.
Site params: direction(horizontal|vertical|diagonal),
sortMode(brightness|hue|saturation), threshold 0..0.5, streakLength 10..300,
intensity 0..1, randomness 0..1."""
import colorsys

import numpy as np
from PIL import Image


def _sort_key(px, mode):
    if mode == "hue":
        return colorsys.rgb_to_hsv(*(px / 255.0))[0]
    if mode == "saturation":
        return colorsys.rgb_to_hsv(*(px / 255.0))[1]
    return float(np.dot(px, [0.299, 0.587, 0.114]))


def _sort_runs(arr, lum, threshold, streak, mode, rng, randomness, reverse=False):
    h, w = lum.shape
    for r in range(h):
        row = arr[r]
        start = None
        for x in range(w + 1):
            above = x < w and lum[r, x] > threshold
            if above and start is None:
                start = x
            end_run = (not above or x - start >= streak) and start is not None
            if end_run:
                run = row[start:x].copy()
                if randomness:
                    jitter = rng.integers(0, max(1, len(run) // 4 + 1))
                    run = np.roll(run, jitter, axis=0)
                keys = np.array([_sort_key(px, mode) for px in run])
                order = np.argsort(keys, kind="stable")
                if reverse:
                    order = order[::-1]
                row[start:x] = run[order]
                start = None


def apply(img, direction="horizontal", sortMode="brightness", threshold=0.25,
          streakLength=100, intensity=1.0, randomness=0.0, seed=0, **_):
    src = img.convert("RGB")
    arr = np.asarray(src, dtype=np.float32).copy()
    rng = np.random.default_rng(seed)
    lum = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    if direction == "vertical":
        arr, lum = arr.transpose(1, 0, 2), lum.T
        _sort_runs(arr, lum, threshold, int(streakLength), sortMode, rng, randomness)
        arr = arr.transpose(1, 0, 2)
    elif direction == "diagonal":
        # sort along NW-SE diagonals
        h, w = lum.shape
        for d in range(-(h - 1), w):
            ys, xs = np.arange(h), np.arange(h) + d
            m = (xs >= 0) & (xs < w)
            ys, xs = ys[m], xs[m]
            dl = lum[ys, xs]
            start = None
            for i in range(len(dl) + 1):
                above = i < len(dl) and dl[i] > threshold
                if above and start is None:
                    start = i
                if (not above or i - start >= streakLength) and start is not None:
                    seg = arr[ys[start:i], xs[start:i]].copy()
                    keys = np.array([_sort_key(px, sortMode) for px in seg])
                    order = np.argsort(keys, kind="stable")
                    arr[ys[start:i], xs[start:i]] = seg[order]
                    start = None
    else:
        _sort_runs(arr, lum, threshold, int(streakLength), sortMode, rng, randomness)
    if intensity < 1.0:
        arr = np.asarray(src, dtype=np.float32) * (1 - intensity) + arr * intensity
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
