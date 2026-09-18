"""Wave Lines — horizontal/vertical wavy scan lines displaced by luminance.
Site params: lineCount 10..150, amplitude 5..50, frequency .5..3,
lineThickness .5..3, direction(h|v), mode, lineColor, bg."""
import math

import numpy as np
from PIL import Image, ImageDraw


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, lineCount=60, amplitude=15, frequency=1.0, lineThickness=1.0,
          direction="horizontal", mode="original", lineColor="#ffffff",
          bg="#000000", **_):
    src = img.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    lum = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    h, w = lum.shape
    out = Image.new("RGB", (w, h), _hex_rgb(bg))
    draw = ImageDraw.Draw(out)
    lc = _hex_rgb(lineColor)
    n = max(10, min(150, int(lineCount)))
    width = max(1, int(round(lineThickness)))

    for i in range(n):
        if direction == "vertical":
            base = (i + 0.5) * w / n
            pts = []
            for y in range(0, h, 2):
                lx = min(w - 1, max(0, int(base)))
                disp = lum[y, lx] * amplitude * math.sin(y * frequency * math.pi / h * 4)
                pts.append((base + disp, y))
        else:
            base = (i + 0.5) * h / n
            pts = []
            for x in range(0, w, 2):
                ly = min(h - 1, max(0, int(base)))
                disp = lum[ly, x] * amplitude * math.sin(x * frequency * math.pi / w * 4)
                pts.append((x, base + disp))
        if mode == "mono":
            col = tuple(int(v) for v in lc)
            draw.line(pts, fill=col, width=width, joint="curve")
        else:
            for j in range(len(pts) - 1):
                px = pts[j]
                sx = min(w - 1, max(0, int(px[0])))
                sy = min(h - 1, max(0, int(px[1])))
                draw.line([px, pts[j + 1]],
                          fill=tuple(int(v) for v in arr[sy, sx]), width=width)
    return out
