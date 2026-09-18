"""Voronoi — cellular tiling from source-sampled seeds. Site params:
cellSize 10..100, edgeWidth 0..1, edgeColor(black|white|darkened),
colorMode(color|grayscale), randomize 0..1."""
import numpy as np
from PIL import Image


def apply(img, cellSize=40, edgeWidth=0.3, edgeColor="0",
          colorMode="color", randomize=0.5, seed=0, **_):
    src = img.convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    h, w = arr.shape[:2]
    cell = max(10, int(cellSize))
    rng = np.random.default_rng(seed)
    gh, gw = h // cell + 2, w // cell + 2
    gy, gx = np.mgrid[0:gh, 0:gw]
    pts = np.stack([(gy + rng.random((gh, gw)) * randomize + (1 - randomize) * 0.5) * cell,
                    (gx + rng.random((gh, gw)) * randomize + (1 - randomize) * 0.5) * cell],
                   axis=-1).reshape(-1, 2)
    yy, xx = np.mgrid[0:h, 0:w]
    d2 = ((yy[..., None] - pts[None, None, :, 0]) ** 2 +
          (xx[..., None] - pts[None, None, :, 1]) ** 2)
    nearest = np.argmin(d2, axis=2)
    # edge = second-nearest minus nearest distance
    d_sorted = np.sort(d2, axis=2)
    gap = np.sqrt(d_sorted[..., 1]) - np.sqrt(d_sorted[..., 0])
    edge = gap < edgeWidth * cell * 0.5

    # cell color = source color at the seed point
    py = np.clip(pts[:, 0].astype(np.int32), 0, h - 1)
    px = np.clip(pts[:, 1].astype(np.int32), 0, w - 1)
    cell_col = arr[py, px]
    out = cell_col[nearest]
    if colorMode == "grayscale":
        g = np.asarray(src.convert("L"), dtype=np.float32)
        cell_g = g[py, px]
        out = np.repeat(cell_g[nearest][..., None], 3, axis=2)

    ec = {"0": (0, 0, 0), "1": (255, 255, 255)}.get(str(edgeColor))
    if ec is not None:
        out[edge] = ec
    else:  # "2" darkened
        out[edge] *= 0.4
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
