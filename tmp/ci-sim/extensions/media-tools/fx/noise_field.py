"""Noise Field — perlin/simplex/worley noise modulating the image.
Site params: noiseType(perlin|simplex|worley), scale 10..100, intensity .5..3,
octaves 1..8, speed .1..3 (animation only — static frame uses seed)."""
import numpy as np
from PIL import Image


def _gradient_noise(h, w, cell, rng):
    """Value-noise octave at `cell`-px lattice, bilinear upsample."""
    gh, gw = max(2, h // cell + 2), max(2, w // cell + 2)
    g = rng.random((gh, gw)).astype(np.float32)
    g_img = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(g_img, dtype=np.float32) / 255.0


def _worley(h, w, cell, rng):
    """Worley (cellular) noise — distance to nearest feature point."""
    gh, gw = max(2, h // cell + 2), max(2, w // cell + 2)
    pts = np.stack([rng.random((gh, gw)) * cell + np.mgrid[0:gh, 0:gw][0][..., None] * cell,
                    rng.random((gh, gw)) * cell + np.mgrid[0:gh, 0:gw][1][..., None] * cell],
                   axis=-1).reshape(-1, 2)
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((yy[..., None] - pts[None, None, :, 0]) ** 2 +
                 (xx[..., None] - pts[None, None, :, 1]) ** 2)).min(axis=2)
    return np.clip(d / (cell * 1.5), 0, 1).astype(np.float32)


def field(h, w, noise_type="perlin", scale=50, octaves=4, seed=0):
    """Fractal noise field in [0,1]. simplex ≈ perlin here (CPU value noise);
    worley is true cellular noise."""
    rng = np.random.default_rng(seed)
    if noise_type == "worley":
        acc, amp, total = np.zeros((h, w), np.float32), 1.0, 0.0
        for o in range(max(1, int(octaves))):
            acc += amp * _worley(h, w, max(4, int(scale / (2 ** o))), rng)
            total += amp
            amp *= 0.5
        return acc / total
    acc, amp, total = np.zeros((h, w), np.float32), 1.0, 0.0
    for o in range(max(1, int(octaves))):
        acc += amp * _gradient_noise(h, w, max(4, int(scale / (2 ** o))), rng)
        total += amp
        amp *= 0.5
    n = acc / total
    # simplex approx: skew the domain a touch for less axis alignment
    if noise_type == "simplex":
        n = np.clip(n * 1.1 - 0.05, 0, 1)
    return n


def apply(img, noiseType="perlin", scale=50, intensity=1.0, octaves=4,
          speed=1.0, distortOnly=False, time=0.0, seed=0, **_):
    """time: seconds — field drifts coherently (speed scales drift rate)."""
    src = img.convert("RGB")
    h, w = src.height, src.width
    n = field(h, w, noiseType, int(scale), int(octaves), seed)
    if time:
        # translate field — coherent drift, not flicker
        d = int(float(time) * float(speed) * int(scale))
        n = np.roll(n, (d, d // 2), axis=(0, 1))
    # displace pixels along the noise gradient; intensity scales displacement
    gy, gx = np.gradient(n)
    disp = float(intensity) * 8
    yy, xx = np.mgrid[0:h, 0:w]
    sy = np.clip((yy + gy * disp * 50).astype(np.int32), 0, h - 1)
    sx = np.clip((xx + gx * disp * 50).astype(np.int32), 0, w - 1)
    arr = np.asarray(src, dtype=np.float32)
    out = arr[sy, sx]
    if not distortOnly:
        # noise overlays as brightness modulation (site shader adds noise * intensity)
        out = out + ((n - 0.5) * 2 * float(intensity) * 30)[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
