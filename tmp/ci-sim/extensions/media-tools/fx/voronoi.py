"""Voronoi — cellular tiling from jittered seed grid. Site params:
cellSize 10..100, edgeWidth 0..1, edgeColor(0=black|1=white|2=original),
colorMode(0=cell average|1=center sample|2=gradient), randomize 0..1."""
import numpy as np
from PIL import Image


def apply(img, cellSize=30, edgeWidth=0.3, edgeColor=0, colorMode=0,
          randomize=0.8, seed=0, **_):
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
    n_cells = pts.shape[0]
    yy, xx = np.mgrid[0:h, 0:w]
    d2 = ((yy[..., None] - pts[None, None, :, 0]) ** 2 +
          (xx[..., None] - pts[None, None, :, 1]) ** 2)
    # nearest + second-nearest
    top2 = np.argpartition(d2, 1, axis=2)[..., :2]
    d_top2 = np.take_along_axis(d2, top2, axis=2)
    nearest = top2[..., 0]
    edge = (np.sqrt(d_top2[..., 1]) - np.sqrt(d_top2[..., 0])) < edgeWidth * cell * 0.5

    if colorMode == 0:  # cell average — mean of source pixels per cell
        flat = nearest.reshape(-1)
        sums = np.stack([np.bincount(flat, weights=arr[..., c].reshape(-1),
                                   minlength=n_cells) for c in range(3)], axis=-1)
        counts = np.bincount(flat, minlength=n_cells)[:, None]
        cell_col = sums / np.maximum(counts, 1)
        out = cell_col[nearest]
    elif colorMode == 2:  # gradient — blend cell color with original by distance ratio
        py = np.clip(pts[:, 0].astype(np.int32), 0, h - 1)
        px = np.clip(pts[:, 1].astype(np.int32), 0, w - 1)
        cell_col = arr[py, px]
        t = (np.sqrt(d_top2[..., 0]) / (np.sqrt(d_top2[..., 0]) + np.sqrt(d_top2[..., 1]) + 1e-6))[..., None]
        out = cell_col[nearest] * (1 - t) + arr * t
    else:  # center sample
        py = np.clip(pts[:, 0].astype(np.int32), 0, h - 1)
        px = np.clip(pts[:, 1].astype(np.int32), 0, w - 1)
        out = arr[py, px][nearest]

    if edgeColor == 0:
        out[edge] = (0, 0, 0)
    elif edgeColor == 1:
        out[edge] = (255, 255, 255)
    else:  # 2 = original pixel at edges
        out[edge] = arr[edge]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
