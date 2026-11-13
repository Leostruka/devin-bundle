import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fx


def _src(w=96, h=64):
    y, x = np.mgrid[0:h, 0:w]
    lum = np.clip(np.exp(-(((x - w / 2) ** 2 + (y - h / 2) ** 2) / (2 * (w / 6) ** 2))) * 255, 0, 255)
    rgb = np.stack([lum, np.full_like(lum, 80), 255 - lum], axis=-1)
    return Image.fromarray(rgb.astype(np.uint8))


def test_registry():
    for name in ("threshold", "blockify", "dots", "contour", "edgeDetection"):
        assert name in fx.EFFECTS


def test_threshold_two_level():
    out = np.asarray(fx.apply("threshold", _src(), {"levels": 2, "mode": "custom"}))
    uniq = set(map(tuple, out.reshape(-1, 3)))
    assert len(uniq) <= 4


def test_threshold_levels_more_bands():
    o2 = np.asarray(fx.apply("threshold", _src(), {"levels": 2})).mean()
    o8 = np.asarray(fx.apply("threshold", _src(), {"levels": 8}))
    assert len(set(map(tuple, o8.reshape(-1, 3)[::37]))) > 3


def test_blockify_block_size():
    out = fx.apply("blockify", _src(), {"blockSize": 16})
    assert out.width % 16 == 0


def _gray_src(w=96, h=64):
    y, x = np.mgrid[0:h, 0:w]
    lum = np.clip(np.exp(-(((x - w / 2) ** 2 + (y - h / 2) ** 2) / (2 * (w / 6) ** 2))) * 255, 0, 255)
    return Image.fromarray(np.stack([lum] * 3, axis=-1).astype(np.uint8))


def test_dots_dark_bg_bright_dot():
    out = np.asarray(fx.apply("dots", _gray_src(), {"mode": "original"}))
    h, w = out.shape[:2]
    center = out[h // 2 - 8:h // 2 + 8, w // 2 - 8:w // 2 + 8].mean()
    corner = out[:8, :8].mean()
    assert center > corner + 20


def test_contour_lines_mode():
    out = np.asarray(fx.apply("contour", _src(), {"fillMode": "lines", "levels": 6}))
    dark_frac = (out.sum(axis=2) < 30).mean()
    assert 0.3 < dark_frac < 1.0


def test_edge_finds_boundary():
    # Hard step edge: left half black, right half white — boundary is a thin
    # vertical line, so ink fraction must be small but nonzero.
    arr = np.zeros((64, 96, 3), dtype=np.uint8)
    arr[:, 48:] = 255
    out = np.asarray(fx.apply("edgeDetection", Image.fromarray(arr),
                              {"algorithm": "sobel", "threshold": 0.4}))
    ink = (out.sum(axis=2) > 60).mean()
    assert 0.001 < ink < 0.2


def test_edge_algorithms_differ():
    s = np.asarray(fx.apply("edgeDetection", _src(), {"algorithm": "sobel"})).sum()
    l = np.asarray(fx.apply("edgeDetection", _src(), {"algorithm": "laplacian"})).sum()
    assert s != l
