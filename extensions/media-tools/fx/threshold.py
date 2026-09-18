"""Threshold — luminance banding. Site params: levels 2..8, thresholdPoint .1-.9,
mode custom(mono)/color(original), fg/bg."""
import numpy as np
from PIL import Image


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, levels=2, thresholdPoint=0.5, mode="color",
          fg="#ffffff", bg="#000000", **_):
    src = img.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    lum = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    levels = max(2, min(8, int(levels)))
    band = np.clip(((lum - thresholdPoint) / max(1e-3, 1 - abs(thresholdPoint - 0.5) * 2)
                    + 0.5) * levels, 0, levels - 1e-6).astype(np.int32)
    t = band / (levels - 1)
    if mode == "custom":
        f, b = np.array(_hex_rgb(fg), np.float32), np.array(_hex_rgb(bg), np.float32)
        out = b[None, None] + t[..., None] * (f - b)[None, None]
    else:
        out = arr * (t / np.clip(lum, 1e-3, None))[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
