import json
import struct
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import glb_input
from fx.ascii_fx import grid, to_threejs


def _make_glb(path):
    """Minimal valid GLB: one red triangle."""
    pos = np.array([[-1, -1, 0], [1, -1, 0], [0, 1, 0]], np.float32)
    idx = np.array([0, 1, 2], np.uint16)
    bin_data = pos.tobytes() + idx.tobytes() + b"\x00\x00"  # pad to 4
    gltf = {
        "asset": {"version": "2.0"},
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36},
            {"buffer": 0, "byteOffset": 36, "byteLength": 6},
        ],
        "buffers": [{"byteLength": len(bin_data)}],
        "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [1, 0, 0, 1]}}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0},
                                    "indices": 1, "material": 0}]}],
        "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}], "scene": 0,
    }
    j = json.dumps(gltf).encode()
    j += b" " * (-len(j) % 4)
    b = bin_data + b"\x00" * (-len(bin_data) % 4)
    total = 12 + 8 + len(j) + 8 + len(b)
    path.write_bytes(b"glTF" + struct.pack("<II", 2, total)
                     + struct.pack("<II", len(j), 0x4E4F534A) + j
                     + struct.pack("<II", len(b), 0x004E4942) + b)


def test_glb_load_renders_triangle(tmp_path):
    p = tmp_path / "tri.glb"
    _make_glb(p)
    out = glb_input.load_glb(p, 100, 80)
    assert out.size == (100, 80)
    arr = np.asarray(out)
    red = (arr[..., 0] > 100) & (arr[..., 1] < 100)
    assert red.sum() > 50  # shaded red triangle present


def test_glb_rejects_non_glb(tmp_path):
    p = tmp_path / "bad.glb"
    p.write_bytes(b"not a glb")
    with pytest.raises(ValueError):
        glb_input.load_glb(p)


def test_glb_empty_geometry(tmp_path):
    p = tmp_path / "empty.glb"
    gltf = {"asset": {"version": "2.0"}, "meshes": [], "accessors": [],
            "bufferViews": [], "buffers": [{"byteLength": 4}]}
    j = json.dumps(gltf).encode()
    j += b" " * (-len(j) % 4)
    b = b"\x00" * 4
    total = 12 + 8 + len(j) + 8 + len(b)
    p.write_bytes(b"glTF" + struct.pack("<II", 2, total)
                  + struct.pack("<II", len(j), 0x4E4F534A) + j
                  + struct.pack("<II", len(b), 0x004E4942) + b)
    with pytest.raises(ValueError, match="no triangle"):
        glb_input.load_glb(p)


def test_threejs_export():
    ramp = np.linspace(0, 255, 48, dtype=np.uint8)
    src = Image.fromarray(np.stack([np.tile(ramp, (32, 1))] * 3, axis=-1))
    g = grid(src)
    html = to_threejs(g, bg="#101010", depth_style="layered")
    assert html.startswith("<!DOCTYPE html>")
    assert "three@0.160.0" in html
    assert "OrbitControls" in html
    assert '"cols":' in html and '"lum":' in html
    assert GRID_DATA_MARKER in html or "const GRID =" in html


def test_threejs_depth_styles():
    src = Image.new("RGB", (32, 32), (128, 128, 128))
    g = grid(src)
    assert "DEPTH = 0" in to_threejs(g, depth_style="flat")
    assert "DEPTH = 0" not in to_threejs(g, depth_style="extreme")


GRID_DATA_MARKER = "GRID.lum"
