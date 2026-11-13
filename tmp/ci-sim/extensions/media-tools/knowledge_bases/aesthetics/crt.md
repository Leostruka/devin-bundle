# CRT (Cathode Ray Tube)

## Visual Anatomy
Artifacts that fool the eye into recognizing "CRT":
1. **Scanlines** — alternating bright/dark horizontal lines from the electron beam raster.
2. **Barrel/pincushion distortion** — the curved glass tube warps the image outward.
3. **Phosphor shadow mask** — subpixel RGB triads (aperture grille / shadow mask / slot mask patterns).
4. **Chromatic aberration** — RGB channels offset horizontally (beam misalignment).
5. **Bloom + vignette** — bright areas bleed light; corners darken.

## The Math / Algorithm
- **Barrel distortion** (per-fragment UV warp, crt-pi):
  `coord -= 0.5; rsq = x² + y²; coord += coord * (k * rsq); coord *= 1 - 0.23k`
  with `k ≈ 0.03–0.1` per axis.
- **Scanlines**: sinusoidal brightness modulation —
  `res *= base + sineAmp * sin(uv.y * π * texHeight)`.
- **Phosphor mask**: multiply RGB by a 3-pixel periodic pattern
  (`shadowMask 1–4`: grille, slot, aperture). Brightness-adaptive scanlines:
  bright pixels bloom wider, dark stay sharp.
- **Gamma roundtrip**: decode sRGB → linear before beam math, re-encode on output
  (`c <= 0.04045 ? c/12.92 : ((c+0.055)/1.055)^2.4`).

## Implementation — Media/Python
Numpy/OpenCV post-pipeline: `cv2.remap` with precomputed barrel-distortion
maps; scanlines = multiply row mask `0.5+0.5*sin`; mask = tile a 3×1 RGB
stripe kernel; chromatic aberration = shift R/B channels ±1–3 px; bloom =
`GaussianBlur` + additive blend. FFmpeg: `geq` expressions or `lensfun`-style
remap + `gblur` chain.

## Implementation — Web/UI
- WebGL fragment shader: distortion → fetch → scanline×mask multiply →
  re-encode gamma (see crt-lottes / crt-pi).
- Cheap CSS-only: `repeating-linear-gradient` scanline overlay +
  `filter: blur` dup layer + `border-radius` + inner `box-shadow` vignette.
- lib: `stefanlegg/crt-fx` (WebGL, zero-dep, multi-pass).

## Sources
- https://github.com/libretro/glsl-shaders/blob/master/crt/shaders/crt-lottes.glsl (public-domain theory shader)
- https://github.com/libretro/glsl-shaders/blob/master/crt/shaders/crt-pi.glsl (parameterized scanline/mask/curvature)
- https://github.com/stefanlegg/crt-fx (WebGL library, tunable params)
- https://github.com/hackr-sh/ghostty-shaders/blob/main/crt.glsl (compact port of Lottes)

## Related local tools
- `grainrad.py --effect vhs` (adjacent analog degradation), `--param scanlines.*`
