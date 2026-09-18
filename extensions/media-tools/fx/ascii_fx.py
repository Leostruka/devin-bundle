"""ASCII effect — grainrad parity.

scale = cell height in px units (site default 2 -> cell 8px).
spacing = extra horizontal gap fraction of cell width.
out_width = target character columns (0 = auto from image).
mode "mono" draws all glyphs in `fg`; "original" samples source color per cell.
"""
import numpy as np
from PIL import Image, ImageDraw

from .charsets import CHARSETS
from .fonts import load_font


def _hex_rgb(c):
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))
    return tuple(c)


def _rgb_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb)


def grid(src, scale=2, spacing=0.0, out_width=0, charset="standard", custom_chars=None):
    """Char/color grid shared by render and text/svg export.
    Returns dict(chars, colors, cell, cell_w, rows, cols)."""
    chars = custom_chars or CHARSETS[charset]
    src = src.convert("RGB")
    cell = max(2, round(4 * scale))
    cell_w = max(1, round(cell * (1 + spacing)))
    cols = out_width or max(1, src.width // cell_w)
    rows = max(1, round(src.height / src.width * cols * cell_w / cell))
    small = src.resize((cols, rows), Image.BILINEAR)
    gray = np.asarray(small.convert("L"), dtype=np.float32) / 255.0
    rgb = np.asarray(small, dtype=np.uint8)
    idx = (gray * (len(chars) - 1)).astype(np.int32)
    return {"chars": [[chars[i] for i in row] for row in idx],
            "colors": rgb, "cell": cell, "cell_w": cell_w,
            "rows": rows, "cols": cols}


def apply(img, scale=2, spacing=0.0, out_width=0, charset="standard",
          custom_chars=None, mode="original", fg="#ffffff", bg="#000000",
          intensity=1.0):
    g = grid(img, scale, spacing, out_width, charset, custom_chars)
    out = Image.new("RGB", (g["cols"] * g["cell_w"], g["rows"] * g["cell"]),
                    _hex_rgb(bg))
    draw = ImageDraw.Draw(out)
    font = load_font(min(g["cell"], g["cell_w"]))
    fg_rgb = _hex_rgb(fg)
    for r in range(g["rows"]):
        y = r * g["cell"]
        for c in range(g["cols"]):
            ch = g["chars"][r][c]
            if ch == " ":
                continue
            color = fg_rgb if mode == "mono" else tuple(int(v) for v in g["colors"][r, c])
            draw.text((c * g["cell_w"], y), ch, fill=color, font=font)
    if intensity < 1.0:
        base = img.convert("RGB").resize(out.size, Image.BILINEAR)
        out = Image.blend(base, out, intensity)
    return out


def to_text(g):
    """Plain-text export — one line per row."""
    return "\n".join("".join(row) for row in g["chars"])


def to_svg(g, mode="original", fg="#ffffff", bg="#000000"):
    """Vector export — monospace <text> spans per row, like the site's SVG builder."""
    w, h = g["cols"] * g["cell_w"], g["rows"] * g["cell"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
             f'viewBox="0 0 {w} {h}">',
             f'<rect width="{w}" height="{h}" fill="{bg}"/>',
             f'<g font-family="Consolas,monospace" font-size="{g["cell"]}">']
    for r in range(g["rows"]):
        y = (r + 1) * g["cell"]
        c = 0
        while c < g["cols"]:
            ch = g["chars"][r][c]
            color = fg if mode == "mono" else _rgb_hex(g["colors"][r, c])
            run = ch
            c += 1
            while c < g["cols"] and (
                    (fg if mode == "mono" else _rgb_hex(g["colors"][r, c])) == color):
                run += g["chars"][r][c]
                c += 1
            if run.strip():
                esc = run.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                x = (c - len(run)) * g["cell_w"]
                parts.append(f'<text x="{x}" y="{y}" fill="{color}" '
                             f'textLength="{len(run) * g["cell_w"]}" lengthAdjust="spacingAndGlyphs">{esc}</text>')
    parts.append("</g></svg>")
    return "".join(parts)


_THREEJS_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ASCII Art 3D Scene</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { overflow: hidden; background: %(bg)s; font-family: monospace; }
    #ascii-scene { width: 100vw; height: 100vh; }
    #info { position: absolute; top: 10px; left: 10px; color: #666;
            font-size: 12px; pointer-events: none; }
  </style>
  <script type="importmap">
  { "imports": {
      "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }
  </script>
</head>
<body>
<div id="ascii-scene"></div>
<div id="info">ASCII 3D — drag to orbit, scroll to zoom</div>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const GRID = %(grid_json)s;
const CELL = %(cell)s, DEPTH = %(depth)s;
const container = document.getElementById('ascii-scene');
const scene = new THREE.Scene();
scene.background = new THREE.Color('%(bg)s');
const camera = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, .1, 5000);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth, innerHeight);
container.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff, .6));
const dl = new THREE.DirectionalLight(0xffffff, 1);
dl.position.set(1,1,2); scene.add(dl);

const group = new THREE.Group();
const W = GRID.cols*CELL, H = GRID.rows*CELL;
for (let r = 0; r < GRID.rows; r++) {
  for (let c = 0; c < GRID.cols; c++) {
    const ch = GRID.chars[r][c];
    if (ch === ' ') continue;
    const cv = document.createElement('canvas');
    cv.width = cv.height = CELL;
    const ctx = cv.getContext('2d');
    ctx.fillStyle = '#' + GRID.colors[r][c].toString(16).padStart(6,'0');
    ctx.font = CELL + 'px Consolas,monospace';
    ctx.textBaseline = 'top';
    ctx.fillText(ch, 0, 0);
    const tex = new THREE.CanvasTexture(cv);
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(CELL,CELL),
      new THREE.MeshBasicMaterial({map:tex, transparent:true}));
    mesh.position.set(c*CELL - W/2, H/2 - r*CELL, GRID.lum[r][c]*DEPTH);
    group.add(mesh);
  }
}
scene.add(group);
camera.position.set(0, 0, Math.max(W,H)*1.1);
controls.update();
(function animate(){ requestAnimationFrame(animate);
  controls.update(); renderer.render(scene, camera); })();
addEventListener('resize', () => {
  camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); });
</script>
</body>
</html>"""


def _hex_int(rgb):
    r, g_, b = (int(v) for v in rgb)
    return (r << 16) | (g_ << 8) | b


def to_threejs(g, bg="#000000", depth_style="layered"):
    """Standalone Three.js HTML — site parity (depthStyle flat|layered|extreme)."""
    import json
    depth = {"flat": 0, "layered": 1, "extreme": 3}.get(depth_style, 1)
    lum = np.asarray(g["colors"], dtype=np.float32).mean(axis=2) / 255.0
    data = {"cols": g["cols"], "rows": g["rows"], "chars": g["chars"],
            "colors": [[_hex_int(g["colors"][r, c]) for c in range(g["cols"])]
                       for r in range(g["rows"])],
            "lum": np.round(lum, 3).tolist()}
    return _THREEJS_TEMPLATE % {"bg": bg, "cell": g["cell"],
                                "depth": depth * g["cell"] * 2,
                                "grid_json": json.dumps(data)}
