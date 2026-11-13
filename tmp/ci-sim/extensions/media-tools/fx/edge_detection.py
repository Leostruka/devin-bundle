"""Edge Detection — sobel/prewitt/laplacian. Site params: algorithm,
threshold .1-.8, lineWidth .5..4, mode, edgeColor, bg."""
import numpy as np
from PIL import Image, ImageFilter

KERNELS = {
    "sobel": (np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], np.float32),
              np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.float32)),
    "prewitt": (np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], np.float32),
                np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], np.float32)),
    "laplacian": (np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], np.float32), None),
}


def _hex_rgb(c):
    c = c.lstrip("#") if isinstance(c, str) else c
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c)


def _conv(lum, k):
    p = np.pad(lum, 1, mode="edge")
    out = np.zeros_like(lum)
    for i in range(3):
        for j in range(3):
            out += k[i, j] * p[i:i + lum.shape[0], j:j + lum.shape[1]]
    return out


def apply(img, algorithm="sobel", threshold=0.3, lineWidth=1.0,
          mode="original", edgeColor="#ffffff", bg="#000000", **_):
    src = img.convert("RGB")
    lum = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    kx, ky = KERNELS.get(algorithm, KERNELS["sobel"])
    mag = np.abs(_conv(lum, kx)) if ky is None else \
        np.hypot(_conv(lum, kx), _conv(lum, ky))
    edge = mag > threshold * mag.max()
    if lineWidth > 1:
        e = Image.fromarray(edge.astype(np.uint8) * 255)
        e = e.filter(ImageFilter.MaxFilter(int(lineWidth) * 2 + 1))
        edge = np.asarray(e) > 0
    out = np.tile(np.array(_hex_rgb(bg), np.float32), (*lum.shape, 1))
    col = np.array(_hex_rgb(edgeColor), np.float32) if mode == "mono" \
        else np.asarray(src, dtype=np.float32)
    out[edge] = col[edge] if mode != "mono" else col
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
