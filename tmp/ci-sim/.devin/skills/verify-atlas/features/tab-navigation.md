# Tab navigation

## Sub-features
`#tabs` renders one `button[data-sec]` per section; clicking sets `aria-selected` and swaps `view-*` visibility.

## How to get to it (user POV)
Top bar, any time. Sections: boot, skills, agents, hooks, scripts, adr, docs, changelog.

## Driving it with curl + headless Edge
- `curl -s http://localhost:8737/ | grep -o 'id="view-[a-z]*"' | sort -u` -> all 8 views exist in the served DOM.
- `curl -s http://localhost:8737/app.js | grep 'data-sec'` -> tab buttons are rendered client-side; count sections in DATA (`SECTIONS` array) matches the 8 views.
- REPL path reflects section: after `cd skills`, `#repl-path` shows `~/skills` (assert via screenshot or by reading the `go()` function: `repl-path` textContent updates on tab switch).

## Gotchas
- All views are in one HTML file - a missing view id means build.py emitted stale markup, not a routing bug.
