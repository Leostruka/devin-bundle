"""GLB input — minimal glTF-Binary loader, no deps beyond numpy/PIL.
Parses JSON+BIN chunks, reads POSITION/indices/NORMAL/baseColor,
renders orthographic with painter's sort + flat shading. Handles the
common case (single/multi-mesh static models); skins/morphs ignored."""
import json
import struct

import numpy as np
from PIL import Image

_COMP = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
         5125: ("I", 4), 5126: ("f", 4)}
_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _accessor(gltf, bins, idx):
    acc = gltf["accessors"][idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    bin_data = bins[bv.get("buffer", 0)]
    fmt, size = _COMP[acc["componentType"]]
    n = _COUNT[acc["type"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or size * n
    out = np.zeros((acc["count"], n), dtype=np.float32)
    for i in range(acc["count"]):
        out[i] = struct.unpack_from("<" + fmt * n, bin_data, off + i * stride)
    return out.reshape(acc["count"]) if n == 1 else out


def _load(path):
    """Return (gltf_json, [bin_bytes per buffer]). Handles GLB binary and
    .gltf JSON with external/data-URI buffers."""
    data = open(path, "rb").read()
    if data[:4] == b"glTF":
        jlen = struct.unpack_from("<I", data, 12)[0]
        gltf = json.loads(data[20:20 + jlen])
        off = 20 + jlen
        blen, btype = struct.unpack_from("<II", data, off)
        bin_data = data[off + 8:off + 8 + blen] if btype == 0x004E4942 else b""
        return gltf, [bin_data]
    try:
        gltf = json.loads(data)
    except json.JSONDecodeError:
        raise ValueError("not a GLB/glTF file")
    from pathlib import Path
    import base64
    bins = []
    for b in gltf.get("buffers", []):
        uri = b.get("uri")
        if uri is None:
            bins.append(b"")
        elif uri.startswith("data:"):
            bins.append(base64.b64decode(uri.split(",", 1)[1]))
        else:
            bins.append((Path(path).parent / uri).read_bytes())
    return gltf, bins


def load_glb(path, width=640, height=480, bg="#000000", wireframe=False):
    """Render GLB to PIL image — orthographic, painter-sorted, lit."""
    gltf, bins = _load(path)
    tris = []
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("mode", 4) != 4:
                continue
            pos = _accessor(gltf, bins, prim["attributes"]["POSITION"])
            idx = (_accessor(gltf, bins, prim["indices"]).astype(np.int64)
                   if "indices" in prim else np.arange(len(pos)))
            col = np.array([200, 200, 200], np.float32)
            mi = prim.get("material")
            if mi is not None and "materials" in gltf:
                bcf = gltf["materials"][mi].get("pbrMetallicRoughness", {}) \
                    .get("baseColorFactor")
                if bcf:
                    col = np.array(bcf[:3], np.float32) * 255
            for t in range(0, len(idx) - 2, 3):
                tri = pos[idx[t:t + 3]]
                tris.append((tri[:, 2].mean(), tri, col))
    if not tris:
        raise ValueError("no triangle geometry in GLB")
    tris.sort(key=lambda x: x[0])  # painter: far first

    all_v = np.concatenate([t[1] for t in tris])
    lo, hi = all_v.min(axis=0), all_v.max(axis=0)
    span = (hi - lo)[:2].max() or 1
    scale = min(width, height) * 0.8 / span
    cx, cy = (lo + hi)[:2] / 2
    out = Image.new("RGB", (width, height), bg)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(out)
    light = np.array([0.4, 0.6, 0.7])
    light = light / np.linalg.norm(light)
    for _, tri, col in tris:
        e1, e2 = tri[1] - tri[0], tri[2] - tri[0]
        n = np.cross(e1, e2)
        nl = np.linalg.norm(n)
        shade = 0.35 + 0.65 * abs(n / nl @ light if nl else 0)
        c = tuple(int(v) for v in np.clip(col * shade, 0, 255))
        pts = [((v[0] - cx) * scale + width / 2,
                height / 2 - (v[1] - cy) * scale) for v in tri]
        if wireframe:
            draw.line(pts + [pts[0]], fill=c, width=1)
        else:
            draw.polygon(pts, fill=c)
    return out
