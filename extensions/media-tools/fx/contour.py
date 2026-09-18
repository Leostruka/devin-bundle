"""Contour — luminance band contours. Site params: fillMode(filled|lines),
levels 3..20, lineThickness .5..3, mode, lineColor, bg."""
import numpy as np
from PIL import Image, ImageFilter


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, fillMode="filled", levels=6, lineThickness=1.0,
          mode="original", lineColor="#ffffff", bg="#000000", **_):
    src = img.convert("RGB")
    levels = max(3, min(20, int(levels)))
    arr = np.asarray(src, dtype=np.float32)
    lum = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    band = (lum * levels).astype(np.int32)
    edge = (np.diff(band, axis=0, prepend=band[:1]) != 0) | \
           (np.diff(band, axis=1, prepend=band[:, :1]) != 0)
    if lineThickness > 1:
        e = Image.fromarray(edge.astype(np.uint8) * 255)
        e = e.filter(ImageFilter.MaxFilter(int(lineThickness) * 2 + 1))
        edge = np.asarray(e) > 0
    if fillMode == "filled":
        t = band / levels
        if mode == "mono":
            lc, bc = np.array(_hex_rgb(lineColor), np.float32), np.array(_hex_rgb(bg), np.float32)
            out = bc[None, None] + t[..., None] * (lc - bc)[None, None]
        else:
            out = arr * (t / np.clip(lum, 1e-3, None))[..., None]
        out[edge] = _hex_rgb(lineColor) if mode == "mono" else np.clip(out[edge] * 0.5, 0, 255)
    else:
        out = np.tile(np.array(_hex_rgb(bg), np.float32), (*lum.shape, 1))
        col = np.array(_hex_rgb(lineColor), np.float32) if mode == "mono" else arr
        out[edge] = col[edge]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
