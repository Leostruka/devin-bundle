# Wired Cyber-UI (Lain/GiTS/NERV Japanese cyberpunk interface)

## Visual Anatomy
1. **Dense monospace data overlays** — kanji/latin log streams, hex dumps,
   wireframe schematics layered over content.
2. **Void-black canvas** — `#000` background; neon only as semantic signal
   (cyan=info, amber=warn, red=alert).
3. **Angular geometry** — `border-radius:0`, clipped corner notches
   (`clip-path` polygons), thin 1px borders.
4. **Glitch/typewriter motion** — text decodes char-by-char, RGB-split flickers,
   blinking block cursors.
5. **Functional brutalism** — every ornament carries data; decoration = crime.

## The Math / Algorithm
Design-token system, not shader math:
```css
--bg:#000; --fg:#d0d0d0;
--cyber-green:#39ff14; --electric-cyan:#00f0ff; --warning-amber:#fcee0a;
border:1px solid; border-radius:0;
font: "Share Tech Mono"/monospace; letter-spacing:.05em;
```
Glitch: `clip-path` slice layers + `translate` jitter + RGB channel copies.
Scanline/grid drift: `repeating-linear-gradient` or animated bg-position.
Contrast: all text ≥ WCAG AA on `#000`.

## Implementation — Media/Python
HUD overlay pass on frames: monospace `cv2.putText` log lines top-left,
timestamp `HH:MM:SS:FF`, thin `cv2.rectangle` 1px corners on tracked objects,
occasional RGB-channel shift ±2px + random row-slice displacement.

## Implementation — Web/UI
- Frameworks (lift patterns): `sysui` (8 themes, 30+ effects),
  `nightwire` (semantic neon tokens, AI-readable DESIGN.md),
  `cyberpunk-ui`/`cybercore-css` (glitch/scanline/glow classes),
  dreadnought design-system doc (90s-anime HUD principles).
- DIY minimum: mono font + 1px borders + `clip-path` notch corners +
  `text-shadow: 0 0 8px var(--accent)` glow + typing/ decode animation.

## Sources
- https://github.com/mtlprog/dreadnought/blob/master/docs/guides/design-system.md (90s anime interface principles: functional brutalism, info density)
- https://github.com/cativo23/nightwire (semantic neon roles on pure #000, WCAG-AA)
- https://github.com/systemprogramdev/sysui (NES.css+xterm+Augmented-UI fusion, terminal panels)
- https://github.com/laddtnov/cyberpunk-ui (zero-dep tokens, glitch/scanline/grid effects)

## Related local tools
- `brutalism.md` (shared: no radius, functional honesty) · `crt.md`/`night-vision.md` (display emulation layers)
