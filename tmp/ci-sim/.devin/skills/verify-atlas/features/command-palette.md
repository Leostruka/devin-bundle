# Command palette

## Sub-features
`Ctrl+K` or `/` opens `#palette` with `#pal-input` + `#pal-results`; commands like `cd skills`, `open <name>`, `help`.

## How to get to it (user POV)
Press `/` anywhere on the page.

## Driving it with curl + headless Edge
- `curl -s http://localhost:8737/ | grep 'id="palette"\|id="pal-input"'` -> DOM present.
- `curl -s http://localhost:8737/app.js | grep -c 'pal-results'` -> handler shipped.
- Palette actions map to `go()` - grep for `open ` handler in app.js.

## Gotchas
- Palette is keyboard-driven; headless screenshot cannot prove the keybinding - only the DOM + handler presence. A full proof needs CDP/Playwright (not vendored here); state that limit in evidence.
