# PC-98 Pixel (Retro Japanese Digital)

## Visual Anatomy
1. **16-color onscreen palette** — chosen from 4096 (12-bit RGB); shared across
   sprites, backgrounds AND UI.
2. **Crosshatched dither gradients** — two colors interleaved in dot patterns to
   fake tones the palette lacks (skin shading, sky gradients).
3. **640×400 high-res** — more detail than 16-bit consoles; thin 1px lineart.
4. **CRT bleed assumed** — art was designed for blurry 0.39mm dot-pitch CRTs;
   sharp LCD pixels make dither look harsher than intended.
5. **Anime CG framing** — visual-novel stills, cel-like figures over textured bg.

## The Math / Algorithm
- **Palette**: 16 entries from 12-bit RGB (`r,g,b ∈ 0..15` → `v*17`).
- **Ordered dither for color mixing**: checkerboard/tiled Bayer between two
  palette colors simulates a third (`red+blue` checker → purple at distance).
  High res makes dense dither patterns viable as gradients.
- **CRT bleed compensation**: horizontal blur ≈0.5px + slight scanlines when
  previewing — raw sharp pixels are NOT how the art was seen.
- Downscale rule: quantize to 16 colors via median-cut/kmeans, THEN dither —
  order matters.

## Implementation — Media/Python
```python
pal = np.array(16_colors_rgb)            # 12-bit palette subset
# per-pixel nearest palette color + Bayer threshold mix of top-2 candidates
q = palette_snap(gray_or_rgb, pal, method='bayer4')
out = cv2.GaussianBlur(q, (0,0), 0.4)    # CRT bleed preview
```
Dither both color channels AND tone — the look IS the palette constraint.

## Implementation — Web/UI
- Canvas: `ctx.imageSmoothingEnabled=false`, `image-rendering: pixelated`,
  quantize via KDTree → 16 entries, Bayer overlay for gradients.
- UI skin: 640×400-canvas mindset — thin 1px borders, 16-color scheme, bitmap
  fonts (e.g. "PixelMplus", k8x12 for kanji), no AA.

## Sources
- https://pixelglade.net.au/blog/posts/2025-08-31-Whats-unique-about-PC98-art.html (PC-88 vs PC-98 color-depth anatomy)
- https://maudcomm.neocities.org/98/art (16-color global palette + dither technique breakdown)
- https://ecruteakforest.com/pc98 (hardware limits: 16 colors, 640×400, CRT context)
- https://pleromanonx86.wordpress.com/2024/09/02/youve-been-looking-at-pc-98-graphics-wrong-your-whole-life/ (dot-pitch/dither intent)

## Related local tools
- `grainrad.py --effect dithering|pixelSort` + `--param process.*` (quantize+dither backbone)
- `dither-1bit.md` (dither kernels) · `crt.md` (display emulation)
