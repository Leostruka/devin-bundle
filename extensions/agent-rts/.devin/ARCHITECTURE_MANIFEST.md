# Architecture Manifest: agent-rts

## 1. Paradigm

- **Primary:** mixed. Python stdlib server (functional collectors +
  `ThreadingHTTPServer`), vanilla-JS three.js frontend (ES modules, no
  build step, no framework).
- **Rules:** observe/relay only. The dashboard reflects real agent
  execution; it never simulates or dispatches fictional work.

## 2. Design Patterns

- **Allowed:** fixed-size particle pools, canvas-baked textures,
  spring/smooth-step animation, accessor injection (`bindFog`, `fogFn`)
  instead of imports across modules.
- **Forbidden:** autonomous work simulation, new dependencies (npm/pip),
  build tooling, framework adoption.

## 3. Style Contracts

- **Formatter / linter:** none enforced; match surrounding file style.
- **Naming:** `snake_case` Python; `camelCase` JS with `PascalCase` classes;
  CSS ids `kebab-case`; localStorage keys prefixed `rts.`.
- **Imports / dependencies:** Python stdlib only; JS uses vendored three.js
  under `web/js/vendor/`; no external packages.
- **Comments/docs:** short header comment per module; WC3-rationale comments
  allowed where behavior mirrors a Warcraft III mechanic.

## 4. Testing Strategy

- **Framework + layout:** `selftest.py` at extension root (14 checks).
- **Coverage philosophy:** contract checks on server endpoints, world sync,
  and feed wiring; visual verification via CDP screenshots.
- **Gates before commit/push:** `python extensions/agent-rts/selftest.py`,
  repo `python audit.py`, `python -m pytest`, CDP reload with clean
  `#booterr`.

## 5. Error Handling

- **Error model:** server fails-open per collector (missing data = empty
  section); frontend guards optional state (`?.`, `??`); `#booterr` surfaces
  fatal JS errors to the user.
- **Logging:** server stderr; frontend console only.
- **Boundaries:** collectors isolated per source; net.js retries websocket.

## 6. Directory Boundaries

- **Layout:** `server.py` + `collectors.py` + `world_bridge.py` = data plane;
  `web/` = static frontend (`js/` modules, `index.html`); `.devin/rts/` =
  runtime state (map, intents, feed, trophies; generated, never edited);
  `LORE.md` = world fiction.
- **Forbidden crossings:** `web/` never reads `.devin/` directly (data flows
  through server snapshot/WS only); server never writes outside `.devin/rts`.

## Non-negotiables

- Dashboard observes and relays real agent execution; no autonomous
  simulation or fictional work dispatch.
- Canonical world semantics come from `extensions/rtsd/world.py`; do not
  fork or contradict them for visuals.
- No AI signatures or Co-Authored-By in any artifact.
- Fog semantics are canonical: 0 never-seen, 1 explored-dimmed, 2 live.
  No presentation change may leak unexplored information.
