"""Halftone — rotated screen dots. Site params: shape(circle|square|diamond|line),
dotScale .5-2, spacing 1..20, angle 0..90, mode bw/color, fg/bg."""
import math

import numpy as np
from PIL import Image, ImageDraw


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, shape="circle", dotScale=1.0, spacing=6, angle=15,
          mode="color", fg="#ffffff", bg="#000000", **_):
    src = img.convert("RGB")
    pitch = max(2, int(spacing))
    # Oversample on the unrotated grid, then rotate the dot layer.
    pad = int(max(src.width, src.height) * 0.4)
    big_w, big_h = src.width + 2 * pad, src.height + 2 * pad
    cols, rows = big_w // pitch + 2, big_h // pitch + 2

    lum_arr = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    layer = Image.new("L", (big_w, big_h), 0)
    d = ImageDraw.Draw(layer)
    for r in range(rows):
        for c in range(cols):
            sx = min(src.width - 1, max(0, c * pitch - pad))
            sy = min(src.height - 1, max(0, r * pitch - pad))
            l = float(lum_arr[sy, sx])
            rr = l * pitch / 2 * dotScale
            if rr < 0.4:
                continue
            cx, cy = c * pitch, r * pitch
            if shape == "square":
                d.rectangle([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
            elif shape == "diamond":
                d.polygon([(cx, cy - rr), (cx + rr, cy), (cx, cy + rr), (cx - rr, cy)], fill=255)
            elif shape == "line":
                d.line([cx, cy - rr, cx, cy + rr], fill=255, width=max(1, int(rr)))
            else:
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
    layer = layer.rotate(-angle, Image.BILINEAR, center=(big_w / 2, big_h / 2))
    layer = layer.crop((pad, pad, pad + src.width, pad + src.height))
    mask = np.asarray(layer, dtype=np.float32) / 255.0

    if mode == "bw":
        f, b = np.array(_hex_rgb(fg), np.float32), np.array(_hex_rgb(bg), np.float32)
        out = b[None, None] + mask[..., None] * (f - b)[None, None]
    else:
        arr = np.asarray(src, dtype=np.float32)
        dark = arr * 0.15
        out = dark + mask[..., None] * (arr - dark)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
