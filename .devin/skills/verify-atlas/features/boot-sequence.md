# Boot sequence

## Sub-features
Typed boot log (`#bootlog`) printing real bundle stats; DEVIN BUNDLE <-> LEOSTRUKA scramble swap after boot; tab bar `#tabs` rendered.

## How to get to it (user POV)
Load `/`. Boot is the landing view (`#view-boot`).

## Driving it with curl + headless Edge
- `curl -s http://localhost:8737/ | grep 'id="bootlog"'` -> present.
- `curl -s http://localhost:8737/app.js | grep -c 'logoSwap'` -> >= 1 (swap code shipped).
- Edge screenshot with `--virtual-time-budget=9000` -> capture post-boot state; logo may show either brand.
- Stat check: skill count in `manifest.json` must equal the number in `#skill-count` region of the built index (grep the dist HTML/JS DATA payload for `"skills": <n>` and compare to manifest `skill_count`).

## Gotchas
- `prefers-reduced-motion` swaps instantly, no scramble - screenshot diff is not a proof of swap; grep `logoSwap` in served app.js instead.
- Serving `file://` breaks nothing obvious but hides path bugs - always http.server.
