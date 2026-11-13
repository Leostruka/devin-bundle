import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fx
from fx.palettes import PALETTES


def _gray(w=64, h=64, v=128):
    return Image.new("RGB", (w, h), (v, v, v))


def test_all_diffusion_algorithms_run():
    for alg in ("floydSteinberg", "atkinson", "jarvisJudiceNinke", "stucki",
                "burkes", "sierra", "sierraTwoRow", "sierraLite"):
        out = fx.apply("dithering", _gray(), {"algorithm": alg, "mode": "mono"})
        assert out.size == (64, 64), alg


def test_ordered_algorithms_run():
    for alg in ("bayer", "bayer2x2", "bayer4x4", "bayer8x8", "bayer16x16",
                "clusteredDot", "blueNoise", "interleavedGradient",
                "crosshatch"):
        out = fx.apply("dithering", _gray(), {"algorithm": alg, "mode": "mono"})
        assert out.size == (64, 64), alg


def test_bayer_matrix_sizes():
    from fx.dithering import _bayer
    for n, vmax in ((2, 3), (4, 15), (8, 63), (16, 255)):
        m = _bayer(n)
        assert m.shape == (n, n) and m.max() == vmax
        assert sorted(m.ravel().tolist()) == list(range(n * n))


def test_floyd_steinberg_coverage():
    # uniform 50% gray, 2 levels -> ~50% coverage is the FS invariant
    out = np.asarray(fx.apply("dithering", _gray(v=128),
                              {"algorithm": "floydSteinberg", "mode": "mono",
                               "fg": "#ffffff", "bg": "#000000"}))
    frac = (out[..., 0] > 127).mean()
    assert 0.35 < frac < 0.65


def test_indexed_palette_membership():
    out = np.asarray(fx.apply("dithering", _gray(v=100),
                              {"algorithm": "bayer", "mode": "indexed",
                               "palette": "gameboy"}))
    pal = set(tuple(p) for p in PALETTES["gameboy"])
    seen = set(map(tuple, out.reshape(-1, 3)))
    assert seen <= pal and len(seen) >= 2


def test_all_palettes_have_declared_sizes():
    from fx.palettes import PALETTE_SIZES
    assert PALETTE_SIZES["gameboy"] == 4
    assert PALETTE_SIZES["pico8"] == 16
    assert PALETTE_SIZES["nes"] == 54
    assert PALETTE_SIZES["newspaper"] == 2


def test_halftone_and_crosshatch_smoke():
    out1 = np.asarray(fx.apply("halftone", _gray(), {"mode": "bw"}))
    assert out1.shape == (64, 64, 3)
    out2 = np.asarray(fx.apply("crosshatch", _gray(v=60), {"layers": 2, "seed": 1}))
    assert out2.shape == (64, 64, 3) and out2.mean() > 5
