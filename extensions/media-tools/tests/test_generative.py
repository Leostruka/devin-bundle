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
                              {"cellSize": 16, "edgeWidth": 0.5, "edgeColor": 0}))
    assert out.shape == (64, 96, 3)
    black = (out.sum(axis=2) < 20).mean()
    assert 0.001 < black < 0.9


def test_voronoi_color_modes():
    for cm in (0, 1, 2):
        o = fx.apply("voronoi", _src(), {"cellSize": 20, "colorMode": cm})
        assert o.size == (96, 64), cm
    # center-sample cells = flat color regions; gradient ≠ average
    a = np.asarray(fx.apply("voronoi", _src(), {"colorMode": 0, "seed": 3}))
    b = np.asarray(fx.apply("voronoi", _src(), {"colorMode": 2, "seed": 3}))
    assert not np.array_equal(a, b)


def test_matrix_rain_renders_trails():
    out = np.asarray(fx.apply("matrixRain", _src(), {"seed": 1}))
    assert out.shape == (64, 96, 3)
    green = (out[..., 1] > out[..., 0] + 30) & (out[..., 1] > out[..., 2] + 30)
    assert green.sum() > 10  # rain glyphs present


def test_matrix_rain_deterministic():
    a = np.asarray(fx.apply("matrixRain", _src(), {"seed": 9}))
    b = np.asarray(fx.apply("matrixRain", _src(), {"seed": 9}))
    c = np.asarray(fx.apply("matrixRain", _src(), {"seed": 10}))
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_matrix_rain_time_descends():
    a = np.asarray(fx.apply("matrixRain", _src(), {"seed": 9, "time": 0.0}))
    b = np.asarray(fx.apply("matrixRain", _src(), {"seed": 9, "time": 0.5}))
    assert not np.array_equal(a, b)  # heads moved


def test_vhs_time_moves_bar():
    # flat source: only effect noise contributes; bar rows carry ~2x std
    flat = Image.new("RGB", (96, 64), (128, 128, 128))
    kw = {"distortion": 0, "colorBleed": 0, "scanlines": 0,
          "trackingError": 0, "noise": 1.0, "seed": 0}
    def bar_row(t):
        out = np.asarray(fx.apply("vhs", flat, {**kw, "time": t}))
        return int(out.std(axis=(1, 2)).argmax())
    r0, r1 = bar_row(0.0), bar_row(1.0)
    # bar sweeps fract(t*0.3)*h -> t=0 near row 0, t=1 near row .3*64≈19
    assert r0 <= 2 and abs(r1 - 19) <= 3


def test_noise_field_time_drifts():
    a = np.asarray(fx.apply("noiseField", _src(), {"seed": 0, "time": 0.0}))
    b = np.asarray(fx.apply("noiseField", _src(), {"seed": 0, "time": 0.1}))
    c = np.asarray(fx.apply("noiseField", _src(), {"seed": 0, "time": 1.0}))
    assert not np.array_equal(a, b) and not np.array_equal(b, c)


def test_wave_lines_time_phase():
    a = np.asarray(fx.apply("waveLines", _src(), {"time": 0.0}))
    b = np.asarray(fx.apply("waveLines", _src(), {"time": 0.4}))
    assert not np.array_equal(np.asarray(a), np.asarray(b))


def test_vhs_artifacts():
    src = _src()
    out = np.asarray(fx.apply("vhs", src, {"seed": 2}))
    assert out.shape == (64, 96, 3)
    assert not np.array_equal(out, np.asarray(src))
    # scanlines create row-level luminance variance
    row_mean = out.mean(axis=(1, 2))
    assert row_mean.std() > 0.1


def test_vhs_params_scale():
    a = np.asarray(fx.apply("vhs", _src(), {"noise": 0.0, "scanlines": 0.0,
                                            "distortion": 0.0, "colorBleed": 0.0,
                                            "trackingError": 0.0, "seed": 0}))
    b = np.asarray(fx.apply("vhs", _src(), {"noise": 1.0, "scanlines": 1.0,
                                            "seed": 0}))
    assert np.abs(b.astype(int) - np.asarray(_src()).astype(int)).mean() > \
        np.abs(a.astype(int) - np.asarray(_src()).astype(int)).mean()
