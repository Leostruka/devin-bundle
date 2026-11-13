---
name: ascii-art
description: Use when generating animated ASCII art for artifacts the agent produces - README banners (SVG), CLI splash screens, loading/404 states or decorative pieces in web pages and terminals. Wraps the ascii.rest library (217 MIT pieces, React components, npx CLI, image-to-ascii).
allowed-tools: [exec, read, write, webfetch]
triggers: [user, model]
---

# ascii-art

## Overview

`ascii.rest` is a free MIT library of 217 animated ASCII pieces plus
block-letter banners. Use it inside artifacts you generate for the user
(READMEs, landing pages, CLIs, terminal output) - never as a dependency
of the bundle itself.

## Choose the surface

| Target artifact | Surface |
|---|---|
| GitHub README / no-JS context | Animated SVG export (self-contained file) |
| React / Next.js / Astro app | `npm install ascii.rest` then `import { Ascii, Banner } from "ascii.rest/react"` |
| Plain HTML, no build | `<script type="module" src="https://ascii.rest/ascii.js"></script>` + `<ascii-art piece="donut">` |
| Terminal preview / CLI splash | `npx ascii.rest <piece>` or `npx ascii.rest banner "<text>" --color f97316,f778ba` (Node 18.3+) |
| Custom piece (one-liner) | the kit: `sea({ palette: "ocean" })`, `spinning(torus())` |
| User photo/logo as ascii | image-to-ascii tool (browser, client-side) |

## Rules

- READMEs get the SVG export, not the script tag - GitHub strips scripts.
- `<Ascii>` renders a `<pre>` with no CSS: set `style={{ lineHeight: 1.2, margin: 0 }}` or rows collapse.
- CDN script tag means a runtime dependency on ascii.rest availability; when the artifact must be self-contained, copy the piece source into the project ("your own copy" mode) or use the SVG.
- Piece names are the slugs on ascii.rest (`night-coast`, `tokyo-rain`, `matrix-rain`); `npx ascii.rest list` prints them all.
- Banners: `<ascii-banner text="x" color="#f97316,#f778ba" shadow="rounded">`; two colors = fade.
- Keep it purposeful: splash, loading, 404, divider - not decoration for its own sake.

## Reference

- Docs: https://ascii.rest/docs/
- Every piece: https://ascii.rest/ (browse grid)
- Source: https://github.com/bas3line/ascii (MIT)
