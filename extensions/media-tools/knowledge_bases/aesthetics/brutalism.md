# Brutalism / Neo-Brutalism (UI·UX)

## Visual Anatomy
1. **Exposed structure** — visible borders on every box; the DOM is the material.
2. **Zero rounding** — `border-radius: 0` everywhere; sharp corners only.
3. **Hard offset shadows** — `box-shadow: 4px 4px 0 #000` (never blurred).
4. **Raw typography** — monospace or heavy grotesk, ALL CAPS, crushed leading
   (`line-height: 0.8–0.9`), giant scale contrast (12px next to 200px).
5. **Asymmetric/broken grid** — overlapping blocks, elements bleeding off-screen;
   high contrast palette (black/white + 1 signal accent).

## The Math / Algorithm
Not shader math — a **constraint system** (design tokens):
```css
--bg: #fff; --ink: #000; --accent: <1 loud color>;
--rule: 2px solid var(--ink);
border-radius: 0; box-shadow: Xpx Ypx 0 var(--ink);  /* blur = 0 */
font: ui-monospace/grotesk; text-transform: uppercase;
```
Rules: ≥40% whitespace OR maximal density — never mid. Links = default blue
underline (`#0000ee`). No gradients, no soft shadows, no icon decoration.
Function-as-aesthetic: if it doesn't inform, remove it.

## Implementation — Media/Python
Poster/graphic analog: thick rule lines, monospace type (PIL `ImageFont`
mono), flat fills, hard crop grids. No anti-aliasing polish.

## Implementation — Web/UI
- HTML: semantic-only, unstyled-looking (`margin: 8px` kept, default links).
- CSS tokens above; grid via `display:grid` + `gap:1px` + `bg:ink` =
  visible hairlines; `transform: rotate(-1deg)` sporadic breaks.
- Neo-brutalist variant: same + playful accent colors, offset hover states.

## Sources
- https://superdesign.dev/styles/brutalism (CSS recipe: tokens, default-blue rule)
- https://alexmayhew.dev/blog/neo-brutalism-developer-guide (hard shadows, thick borders, exposed box model)
- https://socialanimal.dev/blog/brutalist-web-design-strategic/ (béton brut → HTML honesty; Bloomberg/Outline cases)
- https://github.com/devmartinese/awwwards-animations-skill (design-philosophy.md — mono-only, 15–30vw hero, crushed leading)

## Related local tools
- `impeccable` skill (UI polish — opposite pole; use brutalism tokens when user asks for raw/brutalist)
