# Blob Tracking (CV blobs / metaballs)

## Visual Anatomy
1. **Merged goo** — shapes fuse and split smoothly (metaball look).
2. **Contour outlines** — bright stroked perimeters around moving regions.
3. **Centroid dots/labels** — tracked IDs on blob centers.
4. **Threshold posterization** — source reduced to binary before extraction.

## The Math / Algorithm
- **Scalar field / metaballs**: potential `P(x,y) = Σᵢ rᵢ²/((x-xᵢ)²+(y-yᵢ)²)`
  (inverse-square). Surface = iso-contour `P = 1.0`. Two blobs merge when the
  summed field between them crosses the threshold.
- **Marching Squares**: sample the field on a coarse grid → each cell gets a
  4-bit corner mask (16 cases) → interpolate edge crossings → line segments.
  3D analog = Marching Cubes.
- **CV pipeline** (OpenCV `SimpleBlobDetector`): multi-threshold binary images
  → `findContours` per level → group centers by `minDistBetweenBlobs` →
  estimate center+radius → filter by circularity `4πA/P²`, inertia ratio,
  convexity.
- **Motion**: background subtraction (`absdiff` + threshold) or frame diff →
  morphological open/close → contours → track by nearest-centroid.

## Implementation — Media/Python
```python
fg = cv2.absdiff(frame, bg); _, bw = cv2.threshold(fg, 25, 255, 0)
bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, k)
cnts, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```
Metaball render: build field array, `plt.contour(field, levels=[1.0])` or
skimage `measure.find_contours` (marching squares).

## Implementation — Web/UI
- Canvas/GLSL: evaluate `P` per pixel in fragment shader; `step(P,1.0)` fill or
  `smoothstep` edge glow. Marching squares on CPU for crisp vector lines.
- CSS goo trick: `filter: blur(N) contrast(M)` on a parent — cheap metaballs.

## Sources
- https://docs.opencv.org/5.x/d0/d7a/classcv_1_1SimpleBlobDetector.html (multi-threshold + grouping + filters)
- https://github.com/Adam-Mazur/Marching-squares-python (OpenCV marching squares + metaballs)
- https://shuntksh.com/blog/202601/metaball-marching-squares/ (field equation + 16-case lookup)
- https://iradicator.com/2d-surface-reconstruction-marching-squares-with-meta-balls/ (GLSL scalar-field reconstruction)

## Related local tools
- `grainrad.py --effect contour` (edge/contour extraction exists)
