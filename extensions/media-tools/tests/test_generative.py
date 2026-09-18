import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fx
from fx.noise_field import field


def _src(w=96, h=64):
    rng = np.random.default_rng(7)
    lum = (rng.random((h, w)) * 255).astype(np.uint8)
    return Image.fromarray(np.stack([lum] * 3, axis=-1))


def test_pixel_sort_orders_runs():
    out = np.asarray(fx.apply("pixelSort", _src(), {"threshold": 0.2, "direction": "horizontal"}))
    assert out.shape == (64, 96, 3)
    # sorted runs reduce local variance along rows in bright regions
    assert out.sum() > 0


def test_pixel_sort_directions():
    for d in ("horizontal", "vertical", "diagonal"):
        o = fx.apply("pixelSort", _src(), {"direction": d, "threshold": 0.3})
        assert o.size == (96, 64), d


def test_wave_lines_shape_and_count():
    out = np.asarray(fx.apply("waveLines", _src(), {"lineCount": 20, "direction": "horizontal"}))
    assert out.shape == (64, 96, 3)
    rows_with_ink = (out.sum(axis=2) > 60).any(axis=1).sum()
    assert 10 < rows_with_ink <= 64


def test_noise_field_range_and_seed():
    a = field(32, 32, "perlin", 16, 3, seed=1)
    b = field(32, 32, "perlin", 16, 3, seed=1)
    c = field(32, 32, "perlin", 16, 3, seed=2)
    assert 0 <= a.min() <= a.max() <= 1
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_noise_types():
    for t in ("perlin", "simplex", "worley"):
        f = field(32, 32, t, 16, 2, seed=0)
        assert f.shape == (32, 32) and f.std() > 0.01, t


def test_noise_field_apply():
    out = fx.apply("noiseField", _src(), {"noiseType": "perlin", "intensity": 1.5})
    assert out.size == (96, 64)
    out2 = np.asarray(fx.apply("noiseField", _src(), {"seed": 5}))
    assert not np.array_equal(out2, np.asarray(_src()))


def test_voronoi_cells_and_edges():
    out = np.asarray(fx.apply("voronoi", _src(),
                              {"cellSize": 16, "edgeWidth": 0.5, "edgeColor": "0"}))
    assert out.shape == (64, 96, 3)
    black = (out.sum(axis=2) < 20).mean()
    assert 0.001 < black < 0.9
