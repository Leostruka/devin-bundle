---
name: media-tools
description: Use when generating visual artifacts — ASCII art, halftone, dithering, matrix-rain, VHS, pixel-sort, voronoi, and other image/video FX — from images, GIFs, videos, GLB models, or webcam input. Local, offline-first.
argument-hint: What visual artifact should I generate?
triggers: [user]
---

# Media Tools

Local visual-FX generators (grainrad.com pipeline parity). Turns inputs —
images, GIF/MP4/WebM, GLB 3D models, webcam frames — into stylized PNG/JPEG/
SVG/GIF/MP4 artifacts. All offline; JSON on stdout.

## Where it is

- Bundle source: `extensions/media-tools/`
- Installed: `%APPDATA%\devin\extensions\media-tools\` (Windows) or
  `~/.config/devin/extensions/media-tools/` (POSIX)
- Deps: `pillow`, `numpy`, `opencv-python` — pinned in `requirements.txt`,
  install on demand: `python -m pip install -r requirements.txt` (no
  installer venv). `cv2` is only needed for webcam/video input.

## Tools

- `grainrad.py` — unified FX CLI. `--input` (file | `webcam[:N]`), `--effect`,
  `--param k=v` (repeatable; prefix `adjust.`/`process.`/`bloom.`/`grain.`/
  `chromatic.`/`scanlines.`/`vignette.` for pipeline stages), `--preset`,
  `--frames`, `--fps`, `--format png|jpeg|svg|txt|threejs`.
- `ascii_mancer.py` — dense+block ASCII blend → PNG. `--cell-detail`,
  `--cell-block`.
- `glb_input.py` — glTF-Binary loader/renderer (orthographic, flat shading);
  used via `--input model.glb` in grainrad.

Effects (`--list-effects`): `ascii`, `blockify`, `contour`, `crosshatch`,
`dithering`, `dots`, `edgeDetection`, `halftone`, `matrixRain`, `noiseField`,
`pixelSort`, `threshold`, `vhs`, `voronoi`, `waveLines`.

## Flow

```bash
# discover effects/presets
python grainrad.py --list-effects
python grainrad.py --list-presets

# still image → stylized PNG
python grainrad.py --input photo.png --effect halftone --output out.png

# animated input → GIF (10fps default)
python grainrad.py --input clip.mp4 --effect vhs --output out.gif --fps 12

# webcam capture → effect
python grainrad.py --input webcam:0 --effect ascii --output selfie.png
```

Every call prints `{"ok": true, "path": ...}` — verify `ok` before reporting
done. `--self-test` runs synthetic offline asserts per script.

## Boundary

- This skill is for **visual artifact generation** (stylized media).
- UI/UX polish of interfaces → `impeccable`. Diagram artifacts (C4/topology)
  → `architecture-diagrams`. Launch videos from project sites → `brag`.
