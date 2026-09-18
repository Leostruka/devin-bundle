"""Blockify — mosaic blocks. Site params: style(full|shaded|outline),
blockSize 4..20, borderWidth 0..3, mode custom(mono)/color, borderColor, fg/bg."""
import numpy as np
from PIL import Image, ImageDraw


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, style="full", blockSize=8, borderWidth=0, mode="color",
          borderColor="#ffffff", fg="#ffffff", bg="#000000", **_):
    src = img.convert("RGB")
    bs = max(4, min(20, int(blockSize)))
    cols, rows = max(1, src.width // bs), max(1, src.height // bs)
    small = np.asarray(src.resize((cols, rows), Image.BILINEAR), dtype=np.float32)
    lum = np.asarray(src.convert("L").resize((cols, rows), Image.BILINEAR),
                     dtype=np.float32) / 255.0
    out = Image.new("RGB", (cols * bs, rows * bs), _hex_rgb(bg))
    draw = ImageDraw.Draw(out)
    f, b = _hex_rgb(fg), _hex_rgb(bg)
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * bs, r * bs
            col = small[r, c]
            if mode == "custom":
                col = np.array(b) + lum[r, c] * (np.array(f) - np.array(b))
            fill = tuple(int(v) for v in np.clip(col, 0, 255))
            if style == "outline":
                draw.rectangle([x0, y0, x0 + bs - 1, y0 + bs - 1],
                               outline=_hex_rgb(borderColor))
            elif style == "shaded":
                inner = max(1, int(bs * (0.3 + 0.6 * lum[r, c])))
                off = (bs - inner) // 2
                draw.rectangle([x0 + off, y0 + off, x0 + off + inner, y0 + off + inner], fill=fill)
            else:
                draw.rectangle([x0, y0, x0 + bs, y0 + bs], fill=fill)
            if borderWidth > 0 and style != "outline":
                for i in range(int(borderWidth)):
                    draw.rectangle([x0 + i, y0 + i, x0 + bs - 1 - i, y0 + bs - 1 - i],
                                   outline=_hex_rgb(borderColor))
    return out
