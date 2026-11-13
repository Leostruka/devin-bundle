"""Matrix Rain — still-frame of the site's animated rain. Site params:
characterSet, customChars (katakana+digits), density, cellSize 4..32,
spacing 0..1, speed .5..3, trailLength 5..30, rainColor, bgOpacity 0..1
(how much original shows through), glowIntensity 0..2,
direction(down|up|left|right), threshold 0..1 (black point)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .charsets import CHARSETS
from .fonts import load_font

KATAKANA = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789"


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def apply(img, characterSet="custom", customChars=KATAKANA, density=1.0,
          cellSize=12, spacing=0, speed=1.0, trailLength=15,
          rainColor="#00ff00", bgOpacity=0.3, glowIntensity=1.0,
          direction="down", threshold=0.0, time=0.0, seed=0, **_):
    """time: seconds — heads fall coherently (site's `speed` uniform scales it);
    chars flicker ~10Hz independent of fall. Column layout stable per `seed`."""
    src = img.convert("RGB")
    w, h = src.size
    cell = max(4, min(32, int(cellSize)))
    pitch = max(1, cell + int(spacing * cell))
    chars = customChars if characterSet == "custom" else CHARSETS.get(
        characterSet, CHARSETS["standard"])
    rc = np.array(_hex_rgb(rainColor), dtype=np.float32)
    rng = np.random.default_rng(seed)
    font = load_font(cell)

    # dim original — bgOpacity = how much shows through
    base = np.asarray(src, dtype=np.float32) * float(bgOpacity)
    out = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(out)

    trail = max(1, int(trailLength))
    if direction in ("down", "up"):
        cols = range(0, w, pitch)
        span = h
    else:
        cols = range(0, h, pitch)
        span = w
    span_cells = max(1, span // pitch)
    cycle = span_cells + trail
    cols = [c for c in cols if rng.random() < min(1.0, density)]
    for c in cols:
        col_rng = np.random.default_rng(seed + c)
        phase = col_rng.random() * cycle
        head = int((phase + float(time) * float(speed) * 8) % cycle)
        # per-frame char flicker (~10Hz), independent of column phase
        flick = np.random.default_rng(seed + c + int(float(time) * 10) * 7919)
        for t in range(trail):
            pos = head - t if direction in ("down", "left") else head + t
            px = pos * pitch
            if px < 0 or px >= span:
                continue
            fade = (1 - t / trail) ** 1.5
            g = min(1.0, fade * float(glowIntensity) + (0.35 if t == 0 else 0))
            col = tuple(int(v) for v in rc * g)
            ch = chars[flick.integers(0, len(chars))]
            if direction in ("down", "up"):
                draw.text((c, px), ch, fill=col, font=font)
            else:
                draw.text((px, c), ch, fill=col, font=font)
    if threshold:
        arr = np.asarray(out, dtype=np.float32)
        lum = np.asarray(out.convert("L"), dtype=np.float32) / 255.0
        arr[lum < threshold] = 0
        out = Image.fromarray(arr.astype(np.uint8))
    return out
