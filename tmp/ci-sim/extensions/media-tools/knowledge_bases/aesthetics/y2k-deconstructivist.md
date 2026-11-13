# Y2K Deconstructivist (TDR/Tomato/Emigre × F1 livery × sportswear × GiTS)

90s postmodern graphic design: The Designers Republic (Sheffield), Tomato,
Emigre magazine — fused with Nike sportswear graphics, Formula-1 livery, and
industrial cyberpunk anime (Ghost in the Shell). "Destroying minimalism" —
TDR's own phrase for their maximalist rebuild of corporate form.

## Visual Anatomy
1. **Angular custom typography** — sharp, condensed display faces; numerals
   substituted for letters (TDR experimented "how far you could use numbers
   instead of letters before you lost legibility").
2. **Abstract glyph fields** — non-semantic icons, swoosh-like marks,
   barcode/serial elements, sponsor-logo clusters.
3. **Neon saturation on dark/metallic** — acid colors over black, chrome,
   carbon fiber (F1 dark anchor + fluorescent team hue, e.g. Fluro Papaya +
   neon pink "Future Mode" livery).
4. **Speed diagonals** — thin diagonal stripes/sweeping aero curves implying
   motion in static images; forward-thrust condensed wordmarks (F1 rebrand).
5. **Corporate subversion** — appropriated/remixed brand marks
   (TDR's Pepsi→PWEI bastardization), slogans as design ("Work Buy Consume Die").

## The Math / Algorithm
Constraint system + layout transforms:
- Palette: `--bg:#0a0a0f` void/carbon; accents `#fcee0a #ff2a6d #00f0ff
  #39ff14` at full saturation; metallic = vertical gradient `#e8e8e8→#8a8a8a→#f5f5f5`
  + specular highlight band.
- Typography: condensed/angular (Eurostile/Microgramma lineage — actual
  F1/TDR DNA), `transform: skewX(-8..-15deg)` for forward motion,
  tight tracking, numerals styled as mono telemetry (`tabular-nums`).
- Composition: broken asymmetric grid + diagonal element band ~30–45°
  (see constructivism.md — shared ancestor: TDR cites Russian constructivism);
  maximal density — whitespace is the enemy here.
- Glyph layer: generated abstract SVG icons tiled/sparse-scattered.

## Implementation — Media/Python
Poster/frame: dark bg → metallic gradient band (linear interp + specular
stripe via `np.clip` glow) → diagonal speed-line overlay (thin rotated rects
at low alpha) → condensed type rendered skewed (`cv2.warpAffine` shear
matrix `[[1,k,0],[0,1,0]]`, k≈-0.2) → abstract glyph sprites scattered →
optional RGB-split on edges.

## Implementation — Web/UI
```css
:root{ --void:#0a0a0f; --neon:#00f0ff; --hot:#ff2a6d; --lime:#39ff14;
       --amber:#fcee0a; --chrome:linear-gradient(180deg,#e8e8e8,#8a8a8a 45%,#f5f5f5 55%,#6a6a6a); }
body{ background:var(--void); font-family:"Eurostile","Bank Gothic",monospace; }
h1{ font-style:italic; transform:skewX(-10deg); letter-spacing:-.04em;
    text-transform:uppercase; color:var(--neon); }
.speedlines{ background:repeating-linear-gradient(-45deg,transparent 0 18px,rgba(0,240,255,.15) 18px 20px); }
```
Metal text: `background:var(--chrome); -webkit-background-clip:text`.
Glints: sparse animated `box-shadow` flares; grid telemetry numbers in
`font-variant-numeric: tabular-nums` mono.

## Sources
- https://en.wikipedia.org/wiki/The_Designers_Republic (TDR: constructivist roots, corporate subversion, maximalism, Emigre #29)
- https://divinerights.co.uk/products/emigre-issue-29 (Ian Anderson on Emigre #29: "deconstruction of commercial design… destroying minimalism")
- https://www.creativereview.co.uk/designers-republic-remembered/ (numerals-for-letters legibility experiments)
- https://designbycurio.com/learn/f1-formula-one-livery (F1 visual system: dark anchor + fluorescent hue, speed lines, telemetry mono numerals)
- https://www.mclaren.com/racing/formula-1/2022/japanese-grand-prix/downtown-tokyo-x-downtown-woking-how-we-created-future-mode-mcl36/ (cyberpunk/manga livery case: glitch forms, fluorescent pink on carbon)

## Related local tools
- `wired-cyber-ui.md` (shared neon-on-void, angular — this adds chrome/motion/sport)
- `constructivism.md` (diagonal grammar — the direct ancestor)
- `grainrad.py --param chromatic.*` (RGB-split glitch accents)
