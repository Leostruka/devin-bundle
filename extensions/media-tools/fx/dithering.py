"""Dithering — 16 algorithms, 12 palettes, 5 color modes. Grainrad parity.

Error-diffusion family shares one engine; ordered methods share a threshold
matrix path. blueNoise is approximated by a 64x64 interleaved-gradient-noise
field (true void-and-cluster tables are 4KB+ of constants — documented
approximation). crosshatch reuses the hatch overlay on quantized bands.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from .palettes import PALETTES

# (divisor, [(dx, dy, weight), ...]) — standard published kernels.
DIFFUSION = {
    "floydSteinberg": (16, [(1, 0, 7), (-1, 1, 3), (0, 1, 5), (1, 1, 1)]),
    "atkinson": (8, [(1, 0, 1), (2, 0, 1), (-1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 2, 1)]),
    "jarvisJudiceNinke": (48, [(1, 0, 7), (2, 0, 5),
                               (-2, 1, 3), (-1, 1, 5), (0, 1, 7), (1, 1, 5), (2, 1, 3),
                               (-2, 2, 1), (-1, 2, 3), (0, 2, 5), (1, 2, 3), (2, 2, 1)]),
    "stucki": (42, [(1, 0, 8), (2, 0, 4),
                    (-2, 1, 2), (-1, 1, 4), (0, 1, 8), (1, 1, 4), (2, 1, 2),
                    (-2, 2, 1), (-1, 2, 2), (0, 2, 4), (1, 2, 2), (2, 2, 1)]),
    "burkes": (32, [(1, 0, 8), (2, 0, 4),
                    (-2, 1, 2), (-1, 1, 4), (0, 1, 8), (1, 1, 4), (2, 1, 2)]),
    "sierra": (32, [(1, 0, 5), (2, 0, 3),
                    (-2, 1, 2), (-1, 1, 4), (0, 1, 5), (1, 1, 4), (2, 1, 2),
                    (-1, 2, 2), (0, 2, 3), (1, 2, 2)]),
    "sierraTwoRow": (16, [(1, 0, 4), (2, 0, 3),
                          (-2, 1, 1), (-1, 1, 2), (0, 1, 3), (1, 1, 2), (2, 1, 1)]),
    "sierraLite": (4, [(1, 0, 2), (-1, 1, 1), (0, 1, 2)]),
    "atkinson": (8, [(1, 0, 1), (2, 0, 1), (-1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 2, 1)]),
}


def _bayer(n):
    if n == 2:
        return np.array([[0, 2], [3, 1]], np.float32)
    m = _bayer(n // 2)
    return np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])


_CLUSTERED_DOT = np.array([
    [34, 48, 40, 32, 29, 15, 23, 31],
    [42, 58, 56, 53, 21, 5, 7, 10],
    [50, 62, 61, 45, 13, 6, 8, 18],
    [38, 46, 54, 37, 25, 17, 9, 26],
    [33, 41, 43, 30, 35, 22, 19, 27],
    [52, 59, 55, 39, 2, 4, 12, 14],
    [44, 57, 60, 51, 16, 11, 1, 20],
    [36, 49, 47, 42, 28, 24, 3, 63]], np.float32)


def _ign(x, y):
    return (52.9829189 * ((0.06711056 * x + 0.00583715 * y) % 1.0)) % 1.0


def _threshold_matrix(algorithm, matrix_size):
    if algorithm == "bayer" or algorithm.startswith("bayer"):
        if algorithm == "bayer":
            n = int(matrix_size)
        else:
            # site values: bayer2x2 / bayer4x4 / bayer8x8 / bayer16x16
            n = int(algorithm.replace("bayer", "").split("x")[0])
        m = _bayer(n)
        return (m + 0.5) / (n * n), n
    if algorithm == "clusteredDot":
        return (_CLUSTERED_DOT + 0.5) / 64.0, 8
    if algorithm == "interleavedGradient":
        n = 64
        yy, xx = np.mgrid[0:n, 0:n]
        m = np.vectorize(_ign)(xx, yy)
        return m, n
    if algorithm == "blueNoise":
        # Approximation: 64x64 field of interleaved-gradient noise shuffled
        # through a Bayer-8 permutation. True void-and-cluster needs a large
        # precomputed table; IGN+Bayer gives near-identical isotropy here.
        n = 64
        yy, xx = np.mgrid[0:n, 0:n]
        m = np.vectorize(_ign)(xx, yy)
        b = _bayer(8).repeat(8, 0).repeat(8, 1) / 64.0
        return np.sort(m.ravel())[np.argsort(b.ravel())].reshape(n, n), n
    return None, 0


def _ign(x, y):
    return (52.9829189 * ((0.06711056 * x + 0.00583715 * y) % 1.0)) % 1.0


def _bayer(n):
    if n == 2:
        return np.array([[0, 2], [3, 1]], np.float32)
    m = _bayer(n // 2)
    return np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])


def _modulation(h, w, mod_type, freq, amp):
    """Spatial threshold modulation; site ModType options."""
    if not mod_type or amp == 0:
        return np.zeros((h, w), np.float32)
    y, x = np.mgrid[0:h, 0:w]
    if mod_type == "wave":
        m = np.sin((x + y) / max(1, freq) * np.pi / 8)
    elif mod_type == "grid":
        m = np.sin(x / max(1, freq) * np.pi / 4) * np.sin(y / max(1, freq) * np.pi / 4)
    elif mod_type == "radial":
        m = np.sin(np.hypot(x - w / 2, y - h / 2) / max(1, freq) * np.pi / 8)
    elif mod_type == "horizontal":
        m = np.sin(y / max(1, freq) * np.pi / 4)
    elif mod_type == "rgbSplit":
        m = np.sin((x + 2 * y) / max(1, freq) * np.pi / 8)
    else:
        return np.zeros((h, w), np.float32)
    return (m * amp / 10.0).astype(np.float32)


def _displace(arr, h, w, max_displace, angles_deg):
    """Per-channel spatial displacement — Red/Green/Blue Channel 0..360°."""
    out = np.zeros_like(arr)
    for ch, deg in enumerate(angles_deg):
        rad = math.radians(deg)
        dy, dx = round(max_displace * math.sin(rad)), round(max_displace * math.cos(rad))
        out[..., ch] = np.roll(arr[..., ch], (dy, dx), axis=(0, 1))
    return out


def _nearest_palette(px, pal):
    d = ((pal - px) ** 2).sum(axis=1)
    return pal[d.argmin()]


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def _luma(px):
    return float(np.dot(px, [0.299, 0.587, 0.114]))


def apply(img, algorithm="floydSteinberg", intensity=1.0, levels=2,
          matrixSize="8", modType=None, modFrequency=5, modAmplitude=0,
          mode="original", palette=None, colorDepth=0, maxDisplace=0,
          redChannel=0, greenChannel=0, blueChannel=0,
          fg="#ffffff", bg="#000000", **_):
    src = img.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)            # 0..255 RGB
    L = np.asarray(src.convert("L"), dtype=np.float32) / 255.0  # 0..1
    h, w = L.shape
    if maxDisplace:
        arr = _displace(arr, h, w, int(maxDisplace),
                        (redChannel, greenChannel, blueChannel))
        L = np.asarray(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
                       .convert("L"), dtype=np.float32) / 255.0
    levels = max(2, int(levels))
    if colorDepth:
        levels = max(2, min(int(levels), int(colorDepth)))
    f, b = np.array(_hex_rgb(fg), np.float32), np.array(_hex_rgb(bg), np.float32)

    pal = None
    if mode == "indexed":
        pal = np.array(PALETTES.get(palette or "pico8"), np.float32)

    def quant(px):
        """Map a 0..255 RGB pixel to the nearest allowed output color."""
        if pal is not None:
            return _nearest_palette(px, pal)
        l = _luma(px) / 255.0
        if mode == "mono":
            return f if l >= 0.5 else b
        q = np.clip(np.round(l * (levels - 1)) / (levels - 1), 0, 1)
        if mode == "tonal":
            return b + q * (f - b)
        if mode == "original":
            return np.clip(arr_px := px * (q / max(l, 1e-3)), 0, 255)
        # rgb / tonal-rgb fallback: per-channel quantize
        return np.round(px / 255.0 * (levels - 1)) / (levels - 1) * 255.0

    mod = _modulation(h, w, modType, modFrequency, modAmplitude)

    if algorithm in DIFFUSION:
        div, taps = DIFFUSION[algorithm]
        buf = arr.copy()
        gain = float(intensity)
        for y in range(h):
            for x in range(w):
                px = buf[y, x].copy()
                px += mod[y, x] * 255 * (arr[y, x].mean() / 255.0)
                q = quant(np.clip(px, 0, 255))
                err = (np.clip(px, 0, 255) - q) * gain
                buf[y, x] = q
                for dx, dy, wgt in taps:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        buf[ny, nx] += err * wgt / div
        result = buf
    elif algorithm == "crosshatch":
        # Ordered bands + diagonal hatch texture — the site's crosshatch
        # dither entry reuses its crosshatch renderer on quantized bands.
        banded = np.round(arr / 255.0 * (levels - 1)) / (levels - 1) * 255
        yy, xx = np.mgrid[0:h, 0:w]
        hatch = ((xx + yy) % 8 < 4).astype(np.float32) * 40 - 20
        result = np.clip(banded + hatch[..., None] * (1 - np.abs(L[..., None] * 2 - 1)), 0, 255)
    else:
        tm, n = _threshold_matrix(algorithm, matrixSize)
        tile = np.tile(tm, (int(np.ceil(h / n)), int(np.ceil(w / n))))[:h, :w]
        dith = (tile - 0.5) * float(intensity)
        if pal is not None:
            jx = np.clip(np.round(L * (len(pal) - 1) + dith), 0, len(pal) - 1).astype(np.int32)
            result = pal[jx]
        elif mode == "tonal":
            q = np.clip(np.round(np.clip(L + dith / max(levels - 1, 1), 0, 1)
                                 * (levels - 1)) / (levels - 1), 0, 1)
            result = q[..., None] * (f - b)[None, None] + b[None, None]
        elif mode == "mono":
            q = np.clip(L + dith / max(levels - 1, 1), 0, 1)
            q = np.round(q * (levels - 1)) / (levels - 1)
            result = np.where(q[..., None] >= 0.5, f, b)
        else:  # original | rgb — per-channel ordered dither
            q = np.clip(arr / 255.0 + dith[..., None] / max(levels - 1, 1), 0, 1)
            result = np.round(q * (levels - 1)) / (levels - 1) * 255.0
    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))

