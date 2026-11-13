# Constructivism (Soviet Agitprop / Dystopian Poster)

## Visual Anatomy
1. **Structural diagonals** — dominant axis tilted 30–45°; tension, not
   decoration. Rotating a horizontal layout is NOT the same.
2. **3-tone palette** — red + black + paper-white. A 4th color kills the density.
3. **Photomontage cutouts** — photographic figures clipped, pasted onto flat
   geometric fields; visible cut edge does the work.
4. **Type-as-geometry** — bold geometric sans, huge scale, integrated INTO the
   image (angled, wrapped), never a caption below it.
5. **Extreme camera angles** — worm's-eye/bird's-eye photomontage source shots.

## The Math / Algorithm
Layout grammar (Rodchenko/Stepanova/El Lissitzky rules):
- Grid rotated: apply `transform: rotate()` to a whole compositional axis;
  elements still align to the ROTATED grid, not random angles.
- Palette constraint: `#cc0000`/`#0a0a0a`/`#f2ede0` (aged paper) — measure
  usage ≈ 40/20/40.
- Flat shapes only: circles, triangles, rectangles as compositional blocks.
- Halftone photo treatment for pasted figures (see `dither-1bit.md`).

## Implementation — Media/Python
Poster generation: off-white canvas → red/black flat polygons (`cv2.fillPoly`
on rotated coordinates) → halftone-processed photo cutout pasted via mask →
bold sans text rendered along the diagonal axis (rotate canvas, draw, rotate
back). Keep edges hard — no AA polish except on type.

## Implementation — Web/UI
```css
:root{ --red:#cc0000; --ink:#0a0a0a; --paper:#f2ede0; }
body{ background:var(--paper); font-family:"Archivo Black",sans-serif; }
.diagonal{ transform: rotate(-8deg); transform-origin: center; }
.block{ background:var(--ink); color:var(--paper); }
h1{ text-transform:uppercase; letter-spacing:-0.03em; line-height:.85; }
```
Grid: `display:grid` on a rotated wrapper; asymmetry mandatory; zero radius.

## Sources
- https://artdaily.com/news/196575/Soviet-Poster-Art-Style-Is-a-Grammar--Not-a-Filter (3 structural rules: diagonal/palette/photomontage)
- https://videocue.io/looks/constructivism-russian-rodchenko (token list: 30-45° axes, red-black-white, geometric sans)
- https://creativepro.com/russian-constructivism-and-graphic-design/ (movement + designers context)
- https://www.peachpit.com/articles/article.aspx?p=3104528&seqNum=2 (constructivist poster build walkthrough)

## Related local tools
- `brutalism.md` (shared flat/raw grammar — brutalism = digital descendant)
- `grainrad.py --effect halftone` (photo cutout treatment)
