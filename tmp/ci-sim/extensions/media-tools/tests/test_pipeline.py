import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fx.pipeline import adjust, process, postprocess


def _src(w=64, h=64, v=128):
    return Image.new("RGB", (w, h), (v, v, v))


def test_adjust_brightness_contrast():
    assert np.asarray(adjust(_src(), brightness=50)).mean() > 140
    dark = np.asarray(adjust(_src(), brightness=-50)).mean()
    assert dark < 80


def test_adjust_gamma():
    hi = np.asarray(adjust(_src(), gamma=2.0)).mean()
    lo = np.asarray(adjust(_src(), gamma=0.5)).mean()
    assert hi > 128 > lo


def test_adjust_hue_rotates():
    red = Image.new("RGB", (16, 16), (255, 0, 0))
    out = np.asarray(adjust(red, hue=120))
    assert out[..., 1].mean() > out[..., 0].mean()


def test_process_invert():
    assert np.asarray(process(_src(v=255), invert=True)).mean() < 5


def test_process_blur_and_quantize():
    noisy = Image.fromarray(np.random.default_rng(0).integers(0, 255, (32, 32, 3), dtype=np.uint8))
    b = np.asarray(process(noisy, blur=1.0)).std()
    assert b < np.asarray(noisy).std()
    q = process(noisy, quantize=4)
    assert len(set(np.asarray(q).reshape(-1, 3).tolist() if False else map(tuple, np.asarray(q).reshape(-1, 3)))) <= 64


def test_postprocess_each():
    src = _src(v=200)
    b = postprocess(src, bloom={"threshold": 0.5, "soft": 0.1, "intensity": 1.0, "radius": 4})
    assert np.asarray(b).mean() >= 200
    g = postprocess(src, grain={"intensity": 0.5, "size": 1, "speed": 0}, seed=1)
    assert np.asarray(g).std() > 5
    c = postprocess(src, chromatic={"offset": 3})
    assert np.asarray(c).shape == (64, 64, 3)
    s = postprocess(src, scanlines={"opacity": 0.9, "spacing": 2})
    a = np.asarray(s)
    assert a[0].mean() < a[1].mean()
    v = postprocess(src, vignette={"intensity": 0.9})
    va = np.asarray(v)
    assert va[0, 0].mean() < va[32, 32].mean()
