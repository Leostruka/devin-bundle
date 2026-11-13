# 1-bit Dither

## Visual Anatomy
1. **Dot-density = luminance** — no gray pixels; tone lives in dot spacing.
2. **Checkerboard mid-tones** — 50% gray → perfect alternating pattern.
3. **Texture signature** — organic wormy (error diffusion) vs grid-regular (ordered).
4. **Palette snap** — hard quantization, zero intermediate values.

## The Math / Algorithm
Two families:
- **Error diffusion** — push quantization error to unprocessed neighbors
  (raster L→R,T→B). Floyd–Steinberg 1976 kernel:
  ```
          X    7/16
    3/16 5/16  1/16
  ```
  Variants: Atkinson (6/8 propagated → higher contrast, Macintosh look),
  Jarvis–Judice–Ninke (/48, smoother), Stucki, Sierra-3/Lite.
- **Ordered** — threshold matrix tiled over image. Bayer recursion
  `M_2n = 4·M_n + [[0,2],[3,1]]`:
  `M2=[[0,2],[3,1]]` → `out = gray > M[x%n][y%n]·255/n²`.
- **Palette snapping**: `new = argmin_{c∈palette} ||old - c||` (KDTree for n>2).

## Implementation — Media/Python
```python
# Bayer (vectorized): tile M to image size, compare
out = np.where(gray > np.tile(M, reps)*255/n**2, 255, 0)
# FS: scanline loop, err propagation via slicing
# PIL shortcut: im.convert("1")  # FS dither built in
```
FFmpeg: `paletteuse=dither=floyd_steinberg`, `dither=bayer:bayer_scale=4`.

## Implementation — Web/UI
- GLSL: `texture2D(bayerTex, fragCoord/8).r` as threshold; or hash noise.
- JS canvas: typed-array loop with kernel table (see SO impl).
- Preserve pixels: `image-rendering: pixelated`.

## Sources
- https://tannerhelland.com/2012/12/28/dithering-eleven-algorithms-source-code.html (11 kernels + code)
- https://en.wikipedia.org/wiki/Floyd%E2%80%93Steinberg_dithering (error-diffusion matrix)
- https://docs.rs/oxideav-image-filter/latest/src/oxideav_image_filter/dither.rs.html (Bayer+diffusion kernel tables, clean-room)
- https://stackoverflow.com/questions/12422407/ (JS Bayer/Atkinson/FS implementation)

## Related local tools
- `grainrad.py --effect dithering|halftone|dots` (ordered family)
- `ascii_mancer.py` (same 1-bit/dot-matrix lineage — glyph cells instead of dots)
