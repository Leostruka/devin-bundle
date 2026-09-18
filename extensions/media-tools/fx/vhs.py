"""VHS — analog tape artifacts (still-frame of the site's shader).
Site params: distortion 0..1, noise 0..1, colorBleed 0..1,
scanlines 0..1, trackingError 0..1, brightness, contrast.
Shader extras replicated: luma mix .1, r*1.1/b*0.9, vignette,
rolling static bar, horizontal band displacement."""
import numpy as np
from PIL import Image


def apply(img, distortion=0.5, noise=0.3, colorBleed=0.5, scanlines=0.3,
          trackingError=0.2, seed=0, **_):
    src = img.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    h, w = arr.shape[:2]
    rng = np.random.default_rng(seed)

    # --- distortion: per-row horizontal wobble + occasional band tears
    yy, xx = np.mgrid[0:h, 0:w]
    wob = (np.sin(yy / 3.0 + rng.random() * 6.28) *
           rng.random((h, 1)) * distortion * 20)
    # tracking error: a few horizontal bands displaced hard
    n_bands = int(trackingError * 6)
    for _ in range(n_bands):
        y0 = rng.integers(0, h)
        bh = rng.integers(2, max(3, h // 12))
        shift = (rng.random() - 0.5) * trackingError * w * 0.4
        wob[y0:y0 + bh] += shift
    sx = np.clip((xx + wob).astype(np.int32), 0, w - 1)
    out = arr[yy, sx]

    # --- color bleed: horizontal channel smear/shift
    bleed = int(1 + colorBleed * 6)
    out[..., 0] = np.roll(out[..., 0], bleed, axis=1)
    out[..., 2] = np.roll(out[..., 2], -bleed, axis=1)

    # --- scanlines: darken every other row pair
    sl = (np.arange(h)[:, None, None] % 2) * scanlines * 0.4
    out = out * (1 - sl)

    # --- noise: grain + rolling static bar
    out = out + rng.normal(0, noise * 30, out.shape)
    bar_y = int(rng.random() * h)
    bar_h = max(1, h // 50)
    bar = np.abs(yy - bar_y) < bar_h
    out = np.where(bar[..., None],
                   out + rng.normal(0, noise * 60, out.shape), out)

    # --- VHS color characteristics (from site shader)
    luma = (out * [0.299, 0.587, 0.114]).sum(axis=2, keepdims=True)
    out = out * 0.9 + luma * 0.1
    out[..., 0] *= 1.1
    out[..., 2] *= 0.9
    # vignette
    uv_y = (yy / h - 0.5) * 0.5
    uv_x = (xx / w - 0.5) * 0.7
    vig = 1 - np.sqrt(uv_y ** 2 + uv_x ** 2) * 0.5
    out = out * vig[..., None]

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
