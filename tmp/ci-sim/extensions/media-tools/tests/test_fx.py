import sys
from pathlib import Path

import numpy as np
from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ascii_mancer import DETAILED_CHARS, load_font, render_layer


def test_render_layer_fills_cell_grid():
    gray = np.full((64, 64), 1.0, dtype=np.float32)
    cell = 8
    img = render_layer(gray, DETAILED_CHARS, cell, load_font(cell))
    assert img.shape == (64, 64)
    cols_with_ink = (img > 0).any(axis=0).sum()
    span = cols_with_ink / img.shape[1]
    assert span > 0.9, f"glyph span {span:.2f} < 0.90 — chars not on cell grid"


def test_render_layer_luminance_mapping():
    dark = render_layer(np.zeros((16, 16), dtype=np.float32), DETAILED_CHARS, 8, load_font(8))
    bright = render_layer(np.full((16, 16), 1.0, dtype=np.float32), DETAILED_CHARS, 8, load_font(8))
    assert bright.mean() > dark.mean() * 5 + 0.05


def test_font_candidates_load():
    f = load_font(8)
    assert isinstance(f, (ImageFont.FreeTypeFont, ImageFont.ImageFont))
