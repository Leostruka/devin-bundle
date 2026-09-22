# Receipt Paper (Thermal Print)

## Visual Anatomy
1. **1-bit monochrome** — thermal heads only print black dots; gray is faked by dither.
2. **Low-contrast fade** — heat sensitivity varies; edges and fills get washed.
3. **Column artifacts / banding** — print head lines and paper feed jitter.
4. **Fixed width** — 58/80mm rolls ≈ 384/576 px printable width.
5. **Paper texture** — slightly off-white, occasional dust specks.

## The Math / Algorithm
- Quantize to bilevel via **threshold + dither** (thermal = dot-matrix 1-bit):
  ESC/POS reference impl: RGB → strip alpha → `convert("L")` → `ImageOps.invert`
  → `convert("1")` (PIL Floyd–Steinberg default on mode "1").
- ESC/POS raster commands: `GS v 0` (bitImageRaster), `GS ( L` (graphics),
  `ESC *` (bitImageColumn); width in bytes = `(w+7)>>3`, 8 px/byte, MSB first.
- Degradation model: multiply by low-contrast curve `out = 255 - (255-in)*k`
  (k≈0.6–0.8) then dither; add per-row brightness jitter ±3%.

## Implementation — Media/Python
```python
im = Image.open(src).convert("RGB")
im = ImageOps.invert(im.convert("L")).convert("1")   # FS dither
im = ImageOps.invert(im)                              # back to black-on-white
```
Add paper: off-white bg `#f8f6f0`, multiply-noise, optional `cv2.GaussianBlur`
0.4px for ink bleed. Width-normalize to 384/576 px before dithering.

## Implementation — Web/UI
- CSS: `filter: grayscale(1) contrast(0.85)` + SVG feTurbulence paper grain
  overlay; `font-family: monospace`, uppercase, `letter-spacing: 0.05em`;
  torn edges via `clip-path` zigzag.
- Canvas: draw → `getImageData` → 1-bit dither (see dither.md) → putImageData.

## Sources
- https://github.com/python-escpos/python-escpos/blob/development/src/escpos/escpos.py (`image()` API)
- http://python-escpos.readthedocs.io/en/latest/_modules/escpos/image.html (`EscposImage` pipeline: RGBA→L→invert→"1")
- https://python-escpos.readthedocs.io/en/latest/api/escpos.html (bitImageRaster/graphics/column modes)

## Related local tools
- `ascii_mancer.py` (same dot-matrix family; text instead of dots)
- `grainrad.py --effect dithering|dots` (1-bit backbone)
