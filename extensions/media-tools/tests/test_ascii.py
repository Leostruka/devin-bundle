import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fx.charsets import CHARSETS
from fx.ascii_fx import apply as ascii_apply


def _src(w=160, h=120):
    y, x = np.mgrid[0:h, 0:w]
    arr = ((x / w) * 255).astype(np.uint8)
    return Image.fromarray(np.stack([arr] * 3, axis=-1))


def test_charsets_verbatim():
    assert CHARSETS["standard"] == " .:-=+*#%@"
    assert CHARSETS["blocks"] == " ░▒▓█"
    assert CHARSETS["binary"] == " 01"
    assert CHARSETS["detailed"].endswith("%B@$")
    assert CHARSETS["minimal"] == " .:#"
    assert CHARSETS["alphabetic"] == " .icotCOXWM"
    assert CHARSETS["numeric"] == " 1234567890"
    assert CHARSETS["math"].startswith(" .-+")
    assert CHARSETS["emoji"].startswith(" ·")
    assert CHARSETS["custom"] == " .:+*#@"
    assert len(CHARSETS) == 10


def test_ascii_output_dims():
    out = ascii_apply(_src(), scale=2)
    assert out.width > 0 and out.height > 0
    assert out.mode == "RGB"


def test_ascii_charsets_differ():
    outs = [np.asarray(ascii_apply(_src(80, 60), charset=k)).mean() for k in ("binary", "standard", "detailed")]
    assert len(set(round(o, 2) for o in outs)) >= 2


def test_ascii_mono_vs_original():
    src = Image.new("RGB", (80, 60), (200, 30, 30))
    mono = np.asarray(ascii_apply(src, mode="mono", fg="#00ff00"))
    orig = np.asarray(ascii_apply(src, mode="original"))
    ink_m = mono[mono.sum(axis=2) > 60]
    ink_o = orig[orig.sum(axis=2) > 60]
    assert ink_m[:, 1].mean() > ink_m[:, 0].mean()
    assert ink_o[:, 0].mean() > ink_o[:, 1].mean()


def test_ascii_bg_and_intensity():
    out = np.asarray(ascii_apply(_src(), bg="#112233", intensity=1.0))
    dark = out[(np.asarray(_src().convert("L")) < 40)]
    assert dark[:, 2].mean() > dark[:, 0].mean()


def test_ascii_out_width():
    out = ascii_apply(_src(320, 200), out_width=40)
    assert out.width == 40 * round(8 * (1 + 0.0))
