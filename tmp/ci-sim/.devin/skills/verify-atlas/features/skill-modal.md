# Skill modal

## Sub-features
Skill cards in `#skill-grid` (filterable via `#skill-q`); selecting opens `#modal` with `#modal-title` + `#modal-body` rendering that skill's SKILL.md; `#modal-close` dismisses.

## How to get to it (user POV)
`cd skills` tab -> type a filter -> click a card.

## Driving it with curl + headless Edge
- `curl -s http://localhost:8737/ | grep 'id="skill-grid"\|id="modal"'` -> containers present.
- DATA payload: the served app.js/index embeds all skills - grep a known skill name (e.g. `lean-code`) in the served HTML/JS; absence means manifest parsing dropped it.
- Modal open-state proof needs a real DOM - use Edge screenshot on a deep state or assert the modal handler exists (`grep 'modal-body' app.js`).

## Gotchas
- Past bug: phantom-open modal (CSS overriding `hidden`) - if the screenshot shows an empty modal over boot, the regression is back.
