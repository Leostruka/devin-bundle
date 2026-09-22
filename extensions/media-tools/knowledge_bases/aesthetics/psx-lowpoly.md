# PSX/PS1 Lo-Fi 3D

## Visual Anatomy
1. **Vertex wobble/jitter** — geometry snaps to a coarse grid as the camera
   moves (integer vertex positions — no floating point on the PS1 GPU).
2. **Texture warping** — affine texture mapping ignores depth, so textures
   shear/swim on large polygons at oblique angles.
3. **320×240 + nearest neighbor** — true low-res render, real aliasing.
4. **Ordered dither** — the PS1 GPU's 4×4 Bayer dither on the framebuffer.
5. **Hard fog cutoffs** — depth fog hiding the short draw distance.

## The Math / Algorithm
- **Vertex snapping** (fixed-point quantization):
  `xy = clip.xy/clip.w; xy = round(xy·res)/res; clip.xy = xy·clip.w`
  with `res = (160,120)`-ish half-resolution grid.
- **Affine UV**: multiply UV by `w` in vertex stage, divide back in fragment
  (`vUv *= w; frag: uv = vUv/w`) — kills hardware perspective correction.
- **No z-buffer** → painter's sort artifacts; emulate by disabling depth test.
- PS1 dither = specific 4×4 Bayer matrix applied pre-display.

## Implementation — Media/Python
Render path is 3D — use Three.js/GLSL (below). For 2D media mimic:
pixelate (downscale to 320×240 → nearest upscale), Bayer-4 dither,
reduced 15-bit color (`v & 0xF8`), slight horizontal shear on textures.

## Implementation — Web/UI
- Three.js: render to low-res target → nearest upscale; `onBeforeCompile`
  inject vertex-snap + affine (`applyPSXMaterial`-style); post passes:
  4×4 Bayer dither + fog + optional CRT.
- GLSL snippets: vertex-snap quantization function and `vUv*w / vUv/w`
  affine trick — see sources for drop-in code.
- Clamp affine warp near camera (real games tessellated to compensate).

## Sources
- https://github.com/lferreira457/threejs-psx-shader (Three.js impl: snap, affine, pixelation, PS1-GPU dither, fog, CRT)
- https://danielilett.com/2021-11-06-tut5-21-ps1-affine-textures/ (affine mapping via w-component trick)
- https://waffels.neocities.org/guides/psx (vertex snapping shader code, depth-independent variant)
- https://romanliutikov.com/blog/ps1-style-graphics-in-threejs (affine GLSL + integer-vertex explanation)
- https://github.com/libretro/glsl-shaders/blob/master/procedural/tdm-psx-rendering.glsl (full software PSX renderer in GLSL)

## Related local tools
- `glb_input.py` + `grainrad.py` (render GLB → pixelate/dither post-chain)
- `dither-1bit.md` (Bayer), `crt.md` (display layer)
