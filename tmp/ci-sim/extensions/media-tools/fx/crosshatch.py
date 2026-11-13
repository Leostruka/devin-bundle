"""Crosshatch — layered hatch strokes over luminance bands.
Site params: density 2..12, layers 1..4, angle 0..90, lineWidth .5..3,
randomness 0..1, lineColor, bg. Darker regions accumulate more layers."""
import math

import numpy as np
from PIL import Image, ImageDraw


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, density=6, layers=3, angle=45, lineWidth=1.0,
          randomness=0.0, mode="mono", lineColor="#ffffff",
          bg="#000000", seed=0, **_):
    src = img.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    lum = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    h, w = lum.shape
    out = np.tile(np.array(_hex_rgb(bg), np.float32), (h, w, 1))
    rng = np.random.default_rng(seed)
    layers = max(1, min(4, int(layers)))
    spacing = max(2, int(24 / max(1, density)))
    lc = _hex_rgb(lineColor)

    for layer in range(layers):
        # Layer k covers lum < 1 - k/layers: darker areas get more layers.
        band = lum < 1.0 - layer / layers
        ang = math.radians(angle + layer * (90 / max(layers - 1, 1)))
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        corners = [(0, 0), (w, 0), (0, h), (w, h)]
        ts = [cx * nx + cy * ny for cx, cy in corners]
        layer_img = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(layer_img)
        for tt in range(int(min(ts)), int(max(ts)) + 1, spacing):
            if randomness and rng.random() < randomness * 0.3:
                continue
            px, py = nx * tt, ny * tt
            x0, y0 = px - dx * (w + h), py - dy * (w + h)
            x1, y1 = px + dx * (w + h), py + dy * (w + h)
            jit = (rng.random() - 0.5) * randomness * spacing * 0.5 if randomness else 0
            d.line([x0 + nx * jit, y0 + ny * jit, x1 + nx * jit, y1 + ny * jit],
                   fill=255, width=max(1, int(lineWidth)))
        strokes = np.asarray(layer_img) > 0
        paint = strokes & band
        if mode == "mono":
            out[paint] = lc
        else:
            out[paint] = arr[paint]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
