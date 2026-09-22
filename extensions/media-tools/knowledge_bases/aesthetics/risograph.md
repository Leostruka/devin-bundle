# Risograph (Riso Print)

## Visual Anatomy
1. **2–4 spot inks** — not CMYK: fluorescent pink, federal blue, medium green,
   yellow, orange, teal, violet, burgundy. Flat, bright, slightly clashing.
2. **Misregistration** — each color is a separate pass; plates offset a few px.
3. **Coarse halftone** — newspaper-grade screen, visible grain up close.
4. **Multiply overlap** — ink-over-ink creates a real third color
   (blue×yellow→green; pink×blue→purple).
5. **Paper texture + ink bleed** — soy ink spreads into fibers, uneven coverage,
   occasional roller streaks.

## The Math / Algorithm
Per-ink separation pipeline:
1. Split image into N tonal channels (e.g. shadows/mids/highlights or
   luminance bands).
2. Each channel → halftone (coarse Bayer/clustered dot) → grayscale layer
   (black = full ink coverage).
3. Offset each layer by `±(0..8)px` x/y (registration error, random per plate).
4. Composite onto paper tint: `out = paper * Π (1 - inkLayer_i * inkColor_i)`
   (multiply blend); overlapping regions darken into new hues.
5. Finish: paper grain noise + `GaussianBlur σ≈0.4` ink spread.

## Implementation — Media/Python
```python
layers = tonal_split(gray, n=3)                # shadows/mids/highs
for i,(layer,ink) in enumerate(zip(layers, inks)):
    ht = halftone(layer, screen=4)             # coarse screen
    ht = np.roll(ht, (dy[i], dx[i]), (0,1))    # misregister
    paper *= (1 - ht[...,None]*ink_rgb[i])     # multiply ink
out = paper + grain_noise
```

## Implementation — Web/UI
- SVG/CSS: `mix-blend-mode: multiply` on stacked tinted layers,
  `transform: translate(3px,-2px)` per layer for misregister;
  `feTurbulence` grain overlay; duotone via SVG `feColorMatrix`/`feComponentTransfer`.
- Fonts: chunky display sans or hand-drawn; layouts zine-like (asymmetric,
  overprinted borders).

## Sources
- https://bitgrain.app/riso (process anatomy: stencil drum, spot inks, multiply overlaps, coarse halftone)
- https://amix-design.com/asoboad/tools/en/d-2c-print/ (params: misalignment px, grain, ink density, balance)
- https://vayce.app/tools/risograph-effect/ (light/dark ink split, tone lift, misregister)
- https://studio-ity.com/riso/ (2–4 ink separation, shadow/mid/highlight channel mapping)

## Related local tools
- `grainrad.py --effect halftone|dithering` + `grain.` stage
- `dither-1bit.md` (halftone kernels) · `receipt-paper.md` (adjacent print-analog)
