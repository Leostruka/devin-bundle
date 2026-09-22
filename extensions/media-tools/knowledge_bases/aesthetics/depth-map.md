# Depth Map

## Visual Anatomy
1. **Grayscale Z-encode** — near = white (or black), far = opposite; single ramp.
2. **Occlusion bands** — flat regions share one gray level.
3. **Point-cloud sparsity** — exploded views show dots at Z.
4. **Displaced relief** — shallow parallax when the map displaces the image.

## The Math / Algorithm
- Normalize: `z' = (z - zmin)/(zmax - zmin)` → 8-bit. Convention flag
  `invert` (white-near vs black-near).
- **Point cloud**: per pixel → `(x, y, z=g(p)·scale)`, color = source pixel.
  Export PLY (binary little-endian) or render via Three.js `Points`.
- **Displacement mapping** (GPU): ray-march the height map per fragment, or
  cheap `uv' = uv + (h(uv)-0.5)·strength·viewDir` (parallax offset).
- **Distance mapping** (GPU Gems 2 ch.8): precompute 3D distance field
  `dist(p,S)=min d(p,q)` to avoid ray-march overshoot.

## Implementation — Media/Python
- Estimate: MiDaS/`transformers` DPT → `cv2.normalize(→0..255)`.
- Point cloud: `open3d.geometry.PointCloud` from `depth + color` pair
  (zensvi `PointCloudProcessor` pattern); or build `Vertices+Colors` → PLY.
- Displace: `cv2.remap` with `map_x = x + (d-128)·k`.

## Implementation — Web/UI
- Three.js: `BufferGeometry` with position+color per pixel, `PointsMaterial`.
- GLSL: sample `depth` texture in fragment, offset UV (fake parallax) or
  vertex-displace a subdivided plane.
- Reference impl: Haruko386 Pointcloud-Generate (Vue3+Three.js, 6M-point cap,
  PLY export).

## Sources
- https://github.com/Haruko386/Pointcloud-Generate-for-Depth-Estimation (pixel→point reconstruction, PLY export)
- https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-8-pixel-displacement-mapping-distance-functions (distance-map ray intersection)
- https://zensvi.readthedocs.io/en/latest/autoapi/zensvi/transform/PointCloudProcessor.html (Open3D pipeline)
- https://www.comp.nus.edu.sg/~lowkl/publications/lutk_gi2009.pdf (height-field decomposition → displacement)

## Related local tools
- `glb_input.py` (GLB→rendered view could seed a Z-buffer)
- `grainrad.py --param displace.*` (adjacent)
