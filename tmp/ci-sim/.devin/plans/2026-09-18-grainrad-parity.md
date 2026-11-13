# Grainrad Feature-Parity Implementation Plan (media-tools)

> **For agentic workers:** REQUIRED SUB-SKILL: Use /dispatching-parallel-agents (recommended) or /executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `extensions/media-tools/` so the ASCII_Mancer branch's CLI reaches functional parity with grainrad.com (source of the idea), as a composable image-effects pipeline.

**Architecture:** Keep `ascii_mancer.py` as the ASCII effect. Add `fx/` package — one module per effect, a shared `pipeline.py` (adjustments → processing → effect → post-processing → export), and a `grainrad.py` CLI front-end that accepts `--effect`, `--preset`, per-param flags, and emits JSON like the existing tool. Pure Pillow/numpy (WebGPU parity is out of scope; we match output semantics, not the tech).

**Tech Stack:** Python 3, Pillow, numpy. Optional for later phases: imageio/moviepy (GIF/MP4), trimesh+pyrender (GLB), opencv (webcam).

## Global Constraints

- CLI JSON contract preserved: `{"ok": true, "path": ...}` / `{"ok": false, "error": ...}` to stdout.
- Cross-platform (Windows-first); no GPU dependency — CPU only.
- Charsets copied verbatim from grainrad bundle (see Task 2 table).
- Brightness/Contrast params use the site's -100..100 integer range; normalized sliders keep site ranges.
- Every effect module exposes `apply(img: Image.Image, params: dict) -> Image.Image`.
- New deps added to `extensions/media-tools/requirements.txt`, pinned.
- Fix the known pitch bug first (glyph advance != cell width) — all later tasks assume corrected rendering.

## Proposed Modules and Interfaces

```
extensions/media-tools/
  ascii_mancer.py        (living, modified — bugfix + charset/params parity)
  grainrad.py            (living — unified CLI: --effect, --preset, --in, --out, params)
  fx/
    __init__.py          (registry: EFFECTS = {"ascii": fn, "dithering": fn, ...})
    pipeline.py          (adjust(), process(), postprocess(), export())
    charsets.py          (CHARSETS dict verbatim from site)
    ascii_fx.py, dithering.py, halftone.py, dots.py, contour.py,
    pixel_sort.py, blockify.py, threshold.py, edge_detection.py,
    crosshatch.py, wave_lines.py, noise_field.py, voronoi.py,
    matrix_rain.py, vhs.py
  presets.json           (living — the 6 built-in presets, values ported)
  tests/test_fx.py       (living — per-effect smoke + golden-pixel asserts)
```

## Feature Inventory (extracted from grainrad bundle `index-D5s-AdpN.js`)

Input: PNG/JPG/GIF/MP4/WebM/GLB drop, webcam, max file size cap.
15 effects (sidebar registry `i3`): ascii, dithering, halftone, matrixRain, dots, contour, pixelSort, blockify, threshold, edgeDetection, crosshatch, waveLines, noiseField, voronoi, vhs.
Processing (site "Advanced"): invert, brightnessMap, edgeEnhance, blur, quantizeColors, shapeMatching.
Post-processing: bloom(threshold, softThreshold, intensity, radius), grain(intensity, size, speed), chromatic(offset), scanlines(opacity, spacing), vignette(intensity).
Export: png, jpeg, gif(2s@10fps), mp4, svg, txt, threejs(html).
Presets: classic-terminal, matrix, retro-crt, high-detail, minimal, cyberpunk + user custom.

---

### Task 0: Fix glyph-pitch bug (prerequisite)

**Files:**
- Modify: `extensions/media-tools/ascii_mancer.py:34-49`
- Test: `extensions/media-tools/tests/test_fx.py` (create)

**Interfaces:**
- Produces: `render_layer(gray, charset, cell, font)` renders each glyph at `x = col*cell` so output width == `cols*cell`.

- [ ] **Step 1: Failing test** — render a 80-char line at cell=8, assert drawn span ≥ 90% of 640px (fails today: consola advance 4px → 320px span).
- [ ] **Step 2: Implement** — replace join+single `draw.text` with per-cell `draw.text((c*cell, r*cell), ch)` (or measure `font.getlength` once and scale `cell_w` accordingly).
- [ ] **Step 3: Verify** — test green + `--self-test` output fills full canvas width.
- [ ] **Step 4: Commit** `fix(ascii-mancer): draw glyphs on cell grid, not font advance`

### Task 1: Charset + ASCII params parity

**Files:**
- Create (living): `extensions/media-tools/fx/charsets.py`, `fx/ascii_fx.py`
- Modify: `ascii_mancer.py` (delegate to ascii_fx), `requirements.txt` (unchanged — Pillow/numpy already)
- Test: `tests/test_fx.py`

**Interfaces:**
- Produces: `CHARSETS = {"standard": " .:-=+*#%@", "blocks": " ░▒▓█", "binary": " 01", "detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$", "minimal": " .:#", "alphabetic": " .icotCOXWM", "numeric": " 1234567890", "math": " .-+×÷=≠<>≤≥∞∑∏√∫", "emoji": " ·•○◎●◐◑◒◓◔◕◖◗", "custom": " .:+*#@"}`
- Produces: `ascii_apply(img, scale=2, spacing=0.0, out_width=0, charset="standard", custom_chars=None, mono=False, fg=None, bg="#000000", intensity=1.0) -> Image`

- [ ] **Step 1:** write charsets.py + test that every key maps to exact string above.
- [ ] **Step 2:** port ascii render onto corrected render_layer: `--charset` selects set, `--custom-chars` overrides, `--scale` (1..maxCharacterScale), `--spacing` (0..1, letter-spacing fraction), `--out-width` (0=auto), `--mono` (single fg color), `--fg/--bg`, `--intensity` (blend with original).
- [ ] **Step 3:** verify each charset renders distinct output on self-test image.
- [ ] **Step 4:** Commit `feat(media-tools): charset registry + ascii param parity`.

### Task 2: Adjustments pipeline

**Files:** Create `fx/pipeline.py`; Test `tests/test_fx.py`

- [ ] **Step 1:** `adjust(img, brightness=0, contrast=0, saturation=0, hue=0, sharpness=0, gamma=1.0)` — Pillow `ImageEnhance` + LUT gamma + HSV hue rotate; site ranges: b/c/s −100..100, hue 0..360, sharp −?.., gamma .5..2.
- [ ] **Step 2:** `process(img, invert=False, brightness_map=1.0, edge_enhance=0, blur=0.0, quantize=0, shape_match=0.0)` — invert LUT, gaussian blur, posterize for quantize, edge-enhance via UnsharpMask; shape_match approximates edge-preserving smoothing (bilateral-ish via numpy or skip-with-todo flag if cost too high).
- [ ] **Step 3:** `postprocess(img, bloom=None, grain=None, chromatic=None, scanlines=None, vignette=None)` — bloom = bright-pass blur + screen add; grain = gaussian noise per-frame; chromatic = per-channel x-offset; scanlines = dark rows mod spacing/opacity; vignette = radial darkening.
- [ ] **Step 4:** unit tests per stage (deterministic seeds); commit `feat(media-tools): adjustments/processing/post-processing pipeline`.

### Task 3: Unified CLI `grainrad.py`

- [ ] **Step 1:** CLI: `--input/--output/--effect/--preset/--charset/--param value` (repeatable `--param k=v`), same JSON contract; `--list-effects`, `--list-presets`.
- [ ] **Step 2:** pipeline order = input → adjust → process → effect → postprocess → export; `--self-test` preserved.
- [ ] **Step 3:** verify `--effect ascii` output equals ascii_mancer path; commit `feat(media-tools): unified grainrad CLI`.

### Task 4: Export formats

- [ ] **Step 1:** `--format png|jpeg|svg|txt` — svg = `<text>` grid w/ monospace font (port site's SVG builder); txt = plain charset matrix.
- [ ] **Step 2:** tests: svg well-formed (xml parse), txt dimensions match grid.
- [ ] **Step 3:** commit `feat(media-tools): svg/txt export`.

### Task 5: Simple pixel effects (threshold, blockify, dots, contour, edgeDetection)

Per site params:
- threshold: levels 2..8, thresholdPoint .1..9, mode(mono/color), fg/bg.
- blockify: style(full|shaded|outline), blockSize 4..20, borderWidth 0..3, borderColor.
- dots: shape(circle|square|diamond), grid(square|hex), size .5..2, spacing .5..2.
- contour: fillMode(filled|lines), levels 3..20, lineThickness .5..3.
- edgeDetection: algorithm(sobel|prewitt|laplacian), threshold .1..8, lineWidth .5..4.

- [ ] **Step 1:** implement each as `fx/<name>.py` with `apply()`; sobel/prewitt via numpy conv (no scipy dep).
- [ ] **Step 2:** golden-pixel tests (fixed input → assert checksum/invariant per effect).
- [ ] **Step 3:** wire into registry + CLI; commit `feat(media-tools): pixel effects`.

### Task 6: Ordered/error-diffusion effects (dithering, halftone, crosshatch)

- dithering: 16 algorithms incl. floydSteinberg/atkinson/jarvisJudiceNinke/stucki/burkes/sierra(3)/bayer(2/4/8/16)/clusteredDot/blueNoise/interleavedGradient/crosshatch; intensity, levels 2..32, matrixSize select, modulation(wave/grid/radial/horizontal/rgbSplit, freq, amplitude), colorMode(mono/tonal/indexed/rgb/original), palettes(gameboy/cga/nes/pico8/c64/appleII/macintosh/sepia/cyberpunk/newspaper/risograph/custom), colorDepth, maxDisplace, per-channel hue offsets.
- halftone: shape(circle/square/diamond/line), dotScale, spacing, angle 0..90.
- crosshatch: density, layers 1..4, angle, lineWidth, randomness.

- [ ] **Step 1:** error-diffusion engine + Bayer matrices; palette table module.
- [ ] **Step 2:** halftone + crosshatch renderers.
- [ ] **Step 3:** tests per algorithm (uniform gray → known coverage %); commit `feat(media-tools): dithering/halftone/crosshatch`.

### Task 7: Generative effects (pixelSort, waveLines, noiseField, voronoi)

- pixelSort: direction(h/v/diagonal), sortMode(brightness/hue/saturation), threshold, streakLength, intensity, randomness.
- waveLines: lineCount, amplitude, frequency, thickness, direction(h/v).
- noiseField: type(perlin/simplex/worley), scale, intensity, octaves 1..8, speed(anim only).
- voronoi: cellSize, edgeWidth, edgeColor(black/white/darkened), colorMode, randomize.

- [ ] **Step 1:** numpy noise impl (perlin/simplex self-contained; worley via KD-grid).
- [ ] **Step 2:** pixel-sort row/col runs; wave-lines polyline render; voronoi distance field.
- [ ] **Step 3:** tests + commit `feat(media-tools): generative effects`.

### Task 8: Stylized effects (vhs, matrixRain still-frame)

- vhs: distortion, noise, colorBleed, scanlines, trackingError — all 0..1.
- matrixRain (static): charset select + custom, cellSize, spacing, trailLength → single-frame rain overlay (speed/direction matter only in anim).

- [ ] **Step 1:** vhs = channel bleed + band displacement + noise + scanlines.
- [ ] **Step 2:** matrixRain = random glyph columns w/ trail falloff over source.
- [ ] **Step 3:** tests + commit `feat(media-tools): vhs + matrix rain`.

### Task 9: Presets

- [ ] **Step 1:** `presets.json` port of 6 built-ins (values from bundle: e.g. retro-crt = blocks charset + scanlines + grain + brightness10/contrast30 … — extract each preset's settings object during implementation).
- [ ] **Step 2:** `--preset name` merges over defaults; `--save-preset` writes user preset to `~/.config/devin/media-tools/presets.json`.
- [ ] **Step 3:** commit `feat(media-tools): presets`.

### Task 10: GIF input/output + animation

- [ ] **Step 1:** imageio/moviepy dep (pinned); gif in → per-frame pipeline → gif out (2s@10fps default like site); mp4 in → sample frames.
- [ ] **Step 2:** animated matrixRain/noiseField/vhs use `speed`/frame index.
- [ ] **Step 3:** commit `feat(media-tools): gif/mp4 io`.

### Task 11 (stretch): GLB input, webcam, mp4 export, threejs/html export

- GLB → trimesh+pyrender offscreen → pipeline (needs GPU-free raster: pyrender osmesa or matplotlib fallback).
- webcam → opencv capture one frame.
- mp4 export → moviepy; threejs export → port site's HTML template.

### Out of scope (deliberate)

Real-time preview UI, WebGPU backend, PWA install, browser webcam live feed, theme switcher, fullscreen — these are the site's shell, not the effect pipeline. If a web UI is wanted later, that's a separate spec (would suggest the site already does it — value is CLI/scriptable use).

## Self-Review Notes

- Spec coverage: all 15 effects, 5 post-proc, 6 processing params, 10 charsets, palettes, 6 presets, 5 static export formats mapped to tasks.
- Pitch bug fixed in Task 0 before new render code lands.
- matrixRain `speed`, noiseField `speed`, grain `speed` only matter for animation → Task 10.
- Site ASCII is single-layer selectable-charset; ascii_mancer's dual-layer screen-blend is kept as `--dual` extension (superset, not loss).

## Execution status (all tasks complete)

All 12 tasks implemented + green (71 tests). Deviations from plan:

- `imageio`/`moviepy` skipped — used Pillow (gif) + cv2 (mp4), already installed.
- GLB: no trimesh/pyrender — custom zero-dep GLB/glTF parser (`glb_input.py`).
- Animated effects use a coherent `time` param (seconds), not frame index —
  rain falls, VHS bar sweeps (fract(t*0.3)), noise drifts; `speed` scales, `animate=false` freezes.
- `.gltf` (JSON + external/data-URI .bin) also supported.

### Deferred / ignored (annotated, not implemented)

- **Structural, out of scope**: real-time WebGPU render, UI shell (theme/fullscreen/drag-drop).
- **Webcam**: `webcam.py` implemented (cv2.VideoCapture) — untested, no hardware in this env. Deferred per user.
- **Phosphor/crtCurve**: implemented (post stages) — retro-crt/classic-terminal presets use them.
