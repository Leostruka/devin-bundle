"""Dots — halftone-style dot grid. Site params: shape(circle|square|diamond),
gridType(square|hex), size .5..2, spacing .5..2, mode, dotColor, bg."""
import numpy as np
from PIL import Image, ImageDraw


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, shape="circle", gridType="square", size=1.0, spacing=1.0,
          mode="original", dotColor="#ffffff", bg="#000000", **_):
    src = img.convert("RGB")
    pitch = max(3, int(8 * spacing))
    max_r = pitch / 2 * size
    cols, rows = max(1, src.width // pitch), max(1, src.height // pitch)
    small = src.resize((cols, rows), Image.BILINEAR)
    lum = np.asarray(small.convert("L"), dtype=np.float32) / 255.0
    rgb = np.asarray(small, dtype=np.uint8)
    out = Image.new("RGB", (cols * pitch, rows * pitch), _hex_rgb(bg))
    draw = ImageDraw.Draw(out)
    dc = _hex_rgb(dotColor)
    for r in range(rows):
        for c in range(cols):
            rr = max_r * lum[r, c]
            if rr < 0.5:
                continue
            cx = c * pitch + pitch // 2 + (pitch // 2 if gridType == "hex" and r % 2 else 0)
            cy = r * pitch + pitch // 2
            col = dc if mode == "mono" else tuple(int(v) for v in rgb[r, c])
            if shape == "square":
                draw.rectangle([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
            elif shape == "diamond":
                draw.polygon([(cx, cy - rr), (cx + rr, cy), (cx, cy + rr), (cx - rr, cy)], fill=col)
            else:
                draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
    return out
