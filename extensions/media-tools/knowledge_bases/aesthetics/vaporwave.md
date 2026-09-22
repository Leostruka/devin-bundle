# Vaporwave

## Visual Anatomy
1. **Signature gradient** — pink `#ff71ce` → purple `#b967ff` → cyan `#01cdfe`,
   often over sunset orange `#ff9a3a`; soft bleeds, no hard edges.
2. **Infinite grid floor** — neon `#ff00e5` perspective grid receding to horizon.
3. **Classical fragments** — Greek busts/columns, cropped (never whole),
   rendered in cheap 90s CGI.
4. **Temporal collision** — Windows 95 chrome, kanji text, palm trees,
   VHS artifacts in one frame.
5. **Degradation texture** — pixel mosaic, chromatic drift (RGB split),
   soft scanlines, bloom.

## The Math / Algorithm
- Palette tokens (retro-design-system): `--pink:#ff71ce --cyan:#01cdfe
  --purple:#b967ff --green:#05ffa1 --yellow:#fffb96 --bg:#1a0b2e
  --grid:#ff00e5`.
- **Grid floor**: 2D grid texture → `perspective(400px) rotateX(60deg)`
  anchored at bottom → CSS pseudo-element or vertex-projected plane.
- **Photo→vaporwave recipe** (ascii-magic params): pixel mosaic → overlay-blend
  `#ff3cac` at ~34% on midtones → RGB split ±5px → scanlines ~24px period →
  bloom 30% + vignette.
- Sky gradient: multi-stop `linear-gradient(#1a0b2e, #3a1458, #ff71ce,
  #ff9a3a, #ffe87a)`.

## Implementation — Media/Python
```python
im = pixelate(im, px=8)
pink = np.full_like(im, (255,60,172)); im = overlay_blend(im, pink, 0.34)
im[...,0] = np.roll(im[...,0], 5, 1); im[...,2] = np.roll(im[...,2], -5, 1)
im *= scanline_mask(period=24); im = add_bloom(im, 0.3); im *= vignette
```

## Implementation — Web/UI
- Full skin: serif/`"MS PGothic"` for JP text, Times-like serif latin;
  gradient body bg + fixed grid pseudo-element + glow sun disc.
- Statue/column: cropped image with `mix-blend-mode: luminosity` or
  `filter: saturate(0)` + neon `box-shadow`.
- Dialog chrome: Windows-95-style raised borders (`outset` + inner `inset`).

## Sources
- https://github.com/NovusGFX/retro-design-system/blob/main/styles/16-vaporwave/index.html (full CSS impl: palette, perspective grid, gradient)
- https://designmd.app/library/vaporwave-314 (principles: chromatic excess, temporal collision, degradation-as-texture, spatial surrealism)
- https://www.ascii-magic.com/recipes/vaporwave-aesthetic (photo recipe: mosaic + #ff3cac overlay + RGB split + scanlines params)
- https://designmd.app/library/vaporwave-aesthetic (dreamy branch: soft gradients, classical fragments cropped)

## Related local tools
- `grainrad.py --param chromatic.* scanlines.* bloom.* vignette.*` (whole post-chain)
- `crt.md` (shared scanline/VHS substrate) · `y2k-deconstructivist.md` (adjacent 90s revival)
