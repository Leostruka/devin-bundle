import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fx.ascii_fx import grid, to_svg, to_text


def _src(w=80, h=60):
    x = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    return Image.fromarray(np.stack([x] * 3, axis=-1))


def test_txt_export_dims():
    g = grid(_src(), out_width=20)
    txt = to_text(g)
    lines = txt.split("\n")
    assert len(lines) == g["rows"]
    assert all(len(l) == 20 for l in lines)


def test_svg_export_wellformed():
    g = grid(_src(), out_width=20)
    svg = to_svg(g)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    texts = [e for e in root.iter() if e.tag.endswith("text")]
    assert len(texts) > 0


def test_svg_escapes():
    g = {"cols": 1, "rows": 1, "cell": 8, "cell_w": 8,
         "chars": [["<"]], "colors": np.zeros((1, 1, 3), dtype=np.uint8)}
    svg = to_svg(g)
    assert "&lt;" in svg and "<text" in svg
    ET.fromstring(svg)


def test_cli_svg_txt(tmp_path):
    import json
    import subprocess
    cli = Path(__file__).resolve().parent.parent / "grainrad.py"
    src = tmp_path / "in.png"
    _src().save(src)
    for fmt in ("svg", "txt"):
        dst = tmp_path / f"out.{fmt}"
        r = subprocess.run(
            [sys.executable, str(cli), "--input", str(src), "--output", str(dst),
             "--format", fmt], capture_output=True, text=True)
        assert json.loads(r.stdout)["ok"] and dst.stat().st_size > 50
