# Night Vision (Image Intensifier)

## Visual Anatomy
1. **P43 phosphor green** — monochrome green palette (`#7fff7f`-ish ramp).
2. **High-ISO grain** — heavy luminance noise from photocathode amplification.
3. **Bloom/IR halo** — bright sources bleed a soft glow.
4. **Vignette** — round/tube edge darkening (lens is circular).
5. **Lag/persistence** — phosphor decay smears motion (optional).

## The Math / Algorithm
- **Luminance→green**: take intensity `I` (HSV `V` or luma `0.299R+0.587G+0.114B`),
  output `frag = vec3(0, I, 0)` or map through a green LUT
  (`G = I`, `R = B = I·0.25` for softer look).
- **Gain noise**: `I += gauss(0, σ)` per pixel, σ≈0.05–0.15 (scintillation);
  optional temporal flicker ±2%.
- **Bloom**: threshold `I>t` → gaussian blur → additive.
- **Vignette**: multiply by `smoothstep(r_outer, r_inner, dist(uv, center))`.
- **Persistence** (multi-pass): `accum = prev·decay + new·(1-decay)`,
  decay 0.85–0.95 ≈ P31/P43 phosphor lag.

## Implementation — Media/Python
```python
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
noise = np.random.normal(0, 18, g.shape)
out = np.clip(g + noise, 0, 255)
bloom = cv2.GaussianBlur(np.where(out>200, out, 0), (0,0), 6)
frame = cv2.add(out, bloom*0.6); frame *= vignette_mask
rgb = cv2.merge([frame*0.3, frame, frame*0.3])
```

## Implementation — Web/UI
- GLSL single pass: luma → green LUT + hash-noise + vignette. Multi-pass for
  bloom+persistence (phosphor pipeline pattern: beam→decay→bloom→composite).
- CSS-lite: `filter: grayscale() sepia() hue-rotate(90deg) contrast()` +
  radial-gradient vignette overlay.

## Sources
- https://blog.ionoclast.com/2014/04/quick-and-dirty-night-vision-shader-part-1/ (GLSL|ES luma→green, staged build)
- https://dev.to/the_l_man/building-a-multi-pass-phosphor-rendering-pipeline-in-webgl-113o (4-pass decay/bloom pipeline, linear HDR)
- https://github.com/JXUE0/Phosphor-Grid-Render (phosphor glow, noise, flicker, vignette params)
- https://github.com/stefanlegg/crt-fx (mono-green phosphor style + bloom/vignette/noise)

## Related local tools
- `grainrad.py --param grain.* bloom.* vignette.*` (all stages exist)
