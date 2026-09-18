"""ASCII effect — grainrad parity.

scale = cell height in px units (site default 2 -> cell 8px).
spacing = extra horizontal gap fraction of cell width.
out_width = target character columns (0 = auto from image).
mode "mono" draws all glyphs in `fg`; "original" samples source color per cell.
"""
import numpy as np
from PIL import Image, ImageDraw

from .charsets import CHARSETS
from .fonts import load_font


def _hex_rgb(c):
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))
    return tuple(c)


def apply(img, scale=2, spacing=0.0, out_width=0, charset="standard",
          custom_chars=None, mode="original", fg="#ffffff", bg="#000000",
          intensity=1.0):
    chars = custom_chars or CHARSETS[charset]
    src = img.convert("RGB")
    cell = max(2, round(4 * scale))
    cell_w = max(1, round(cell * (1 + spacing)))
    cols = out_width or max(1, src.width // cell_w)
    rows = max(1, round(src.height / src.width * cols * cell_w / cell))

    small = src.resize((cols, rows), Image.BILINEAR)
    gray = np.asarray(small.convert("L"), dtype=np.float32) / 255.0
    rgb = np.asarray(small, dtype=np.uint8)
    idx = (gray * (len(chars) - 1)).astype(np.int32)

    out = Image.new("RGB", (cols * cell_w, rows * cell), _hex_rgb(bg))
    draw = ImageDraw.Draw(out)
    font = load_font(min(cell, cell_w))
    fg_rgb = _hex_rgb(fg)
    for r in range(rows):
        y = r * cell
        for c in range(cols):
            ch = chars[idx[r, c]]
            if ch == " ":
                continue
            color = fg_rgb if mode == "mono" else tuple(int(v) for v in rgb[r, c])
            draw.text((c * cell_w, y), ch, fill=color, font=font)

    if intensity < 1.0:
        base = src.resize(out.size, Image.BILINEAR).convert("RGB")
        out = Image.blend(base, out, intensity)
    return out
