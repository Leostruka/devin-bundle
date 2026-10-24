# DevinCraft / DevTycoon Orchestrator: Game Design & Architecture

Extension: `extensions/agent-rts/` (canon session name *the Workshop*). A
WebGL2/Three.js PBR real-time-strategy/tycoon view over the same live bundle
state that powers `rtsd`.

Prime directive (inherited from the v2 GDD): **no invented features**. Every
game entity traces to a real bundle or Devin CLI surface. Canon rule
(inherited): the game **observes, projects, and relays; it never dispatches**.
Surfaced intents are routed to orchestrator skills (leo / ask-bundle), which
decide whether to act.

## 0. Relation to the existing `rtsd` system

`extensions/rtsd/` already ships the full v2 protocol stack:

- `rtsd.py`: stdlib daemon on `127.0.0.1:8797`: `POST /event`,
  `GET /snapshot|/health|/decisions|/score|/sessions|/replay`,
  `POST /decisions/<id>/answer`, `POST /intent`, `GET /ws` (vendored RFC 6455).
- `world.py`: event-sourced world model (heroes = `agents/*.md` profiles,
  11 buildings, 72x54 tile map, tool-to-building map, order queues, quests).
- `scripts/rts-emit.py`: hook tap: POSTs to rtsd, **falls back to appending
  `.devin/rts/events.jsonl` directly**, so the JSONL log is the durable
  source of truth whether or not a daemon is up.
- `scripts/rts-intents.py`: `UserPromptSubmit` hook: surfaces
  `.devin/rts/intents/*.json` (`status: "pending"` becomes `additionalContext`,
  marked `surfaced` exactly once).
- `scripts/rts-decision.py`: `--create/--wait` decision bridge
  (`.devin/rts/decisions/<id>.json` + `<id>.json.response`), fail-closed.
- `web/`: Canvas 2D engine + raw-WebGL `engine3d.js` + dual-theme
  (`battlefield` / `office`) sprite registry.

**Decision: agent-rts is a sibling, not a fork.** It reuses the state root
(`.devin/rts/`), the event log, the intent/decision file queues, and imports
`world.py` for an identical world projection, so the existing hooks,
mailbox delivery, and decision bridge keep working unchanged. It replaces
only two things: (a) the server gains **repository telemetry collectors**
(the git/gh/bundle bridges the mandate requires), (b) the client is a new
Three.js PBR scene instead of Canvas 2D.

| Concern | v2 (`rtsd`) | v3 (`agent-rts`) |
|---|---|---|
| Server | stdlib HTTP+WS, events/snapshot | same shape + `collectors.py` telemetry + `POST /cmd` control |
| World model | `world.py` (event-sourced) | **imported unchanged** via `world_bridge.py`; repo telemetry layered on top, never inside `World.apply` (purity contract preserved) |
| Renderer | Canvas 2D + optional raw WebGL | Three.js PBR (Standard/Physical materials, IBL, PCFSoft, SSAO, tilt-shift bokeh) |
| Themes | sprite re-skins | full scene swap (medieval vs office geometry/materials/lights) |
| Port | 8797 (`RTSD_PORT`) | 8798 (`AGENT_RTS_PORT`), can run beside rtsd on the same `.devin/rts/` root |

## 1. Mechanic to CLI/bundle mapping

### 1.1 Units (StarCraft asymmetry)

| Game unit | Real surface | Stats source |
|---|---|---|
| Scout (fast, cheap) | `researcher` / `subagent_explore`, `swe-2-medium` | `agents/*.md` allowed-tools + `data/bundle-models.json` (`medium_role_model`) |
| Engineer (workhorse) | `implementer`, parent session `swe-2-high` | `default_parent_model` |
| Heavy architecture unit | `architect`/`tech-lead`, `swe-2-max` | `max_role_model`, `default_subagent_model` |
| Cleric/support | `qa-ci`, `reviewer` | profiles (read-only + exec gates) |
| Peasant/worker | a live hook tap (rts-emit firing) | `world.py` `WORKER_WINDOW_S` |
| Minion (temporary shell) | short-lived subprocess session | `world.py` `MINION_TTL_S` |

Unit tier = effort level (`medium`/`high`/`max`), not model size. Same
convention as `bundle-models.json` and the v2 hero table.

### 1.2 Resources

| Resource | Real surface | Collector |
|---|---|---|
| Minerals (gold) | token spend / cost: chars / 4 across `events.jsonl` payloads + ledger sizes | `world.py` already computes; exposed in snapshot `econ` |
| Vespene gas | **free context-window headroom**: `context_window` per model in `bundle-models.json` minus estimated usage; under 10% triggers compaction/handoff alert | `collectors.context_gas()` |
| Supply (food) | local CPU/RAM + concurrent subagent count vs `SUPPLY_CAP` (8) | `collectors.supply()` |
| Lumber (alt bar) | repo dirty-file count (`git status --porcelain`) | `collectors.git()` |

### 1.3 Buildings / stations

| Building (medieval) | Station (office) | Real surface |
|---|---|---|
| Castle / Town Hall | Server rack / main desk | `main` branch, repo root |
| Forge / Runeforge | Planning desk | `extensions/ai-tools/prompt_compiler.py` writes `.devin/scratch/optimized_ready.md` |
| Watchtower / firewall gate | LayaGuard gate | `extensions/laya-tools/laya_cli.py predict --preset guard` + PreToolUse gates |
| Order counter / tavern | Cafe-Mania ticket rail | `gh issue list` + `.devin/scratch/` issues (SLA = issue age) |
| Barracks | Spawn pod | `run_subagent` dispatches |
| Library | Knowledge base | `skill` invocations, `data/bundle-models.json`, KBs |
| Vault | Ledger archive | `.devin/ledgers/` gates ledgers |
| Portal | Extensions bay | `extensions/*` activity |
| Altar | Test shrine | `pytest` runs, `tests/validation`/`tests/held-out` |
| Marketplace | MCP bazaar | `mcp_*` tool calls |

`TOOL_TO_BUILDING` and `BUILDING_AFFINITY` in `world.py` already encode this;
agent-rts renders the same sites in 3D.

### 1.4 Progress particles (Game Dev Tycoon style)

Emitted by stations while work happens; mapped to event types:

| Bubble color | Event | Source |
|---|---|---|
| Blue (Design/Brain) | skill invoke, planning, ask_user_question | `hook.posttooluse` tool=`skill`/`ask_user_question` |
| Green (Code/Muscle) | write/edit/exec success | `hook.posttooluse` tool in {write,edit,exec} success |
| Purple (Research) | read/grep/web_search/mcp reads | read-family tools |
| Red (Bug/Failure) | nonzero exit, test fail, gate deny | `tool_response.success==false`, decision deny, laya guard block |

### 1.5 Cafe-Mania order queue

GitHub issues + local scratch issues become ticket cards on a rail with
cooking-time SLA (age since creation). Dragging a ticket onto the Forge
station issues a `forge_ticket` command which runs
`prompt_compiler.py --draft` with a generated spec, writes
`optimized_ready.md`, and flips the ticket to "served".

## 2. WebSocket protocol (`GET /ws`)

Frames are JSON text both ways. One socket carries snapshot then deltas.

### 2.1 Server to client

```jsonc
// first frame after upgrade
{"type": "hello", "server": "agent-rts", "v": 1, "token_required": true,
 "port": 8798}

// full state, sent on join and on request
{"type": "snapshot", "ts": 1792855000.0,
 "world": { /* world.py snapshot(): units, buildings, map, quests, econ, feed */ },
 "repo": {
   "branch": "milestone/v3.8.0", "dirty": ["path"],
   "worktrees": [{"path": "...", "branch": "..."}],
   "issues": [{"n": 12, "title": "...", "age_s": 3600, "labels": []}],
   "forge_queue": {"optimized_ready": true, "mtime": 0.0},
   "ledgers": [{"name": "x.md", "open_gates": 3}],
   "gas": {"context_window": 262144, "used_est": 140000, "free_pct": 46.6},
   "supply": {"used": 3, "cap": 8, "cpu_pct": 22.0, "ram_pct": 61.0}
 },
 "decisions": [ /* pending decision files */ ],
 "intents":  [ /* recent surfaced/pending intents */ ]}

// incremental world change (2s tick or on-event)
{"type": "delta", "ts": 0.0, "upsert": {"units": [], "buildings": [],
 "feed": []}, "remove": {"units": ["id"]}}

// transient visual effects, no world state
{"type": "fx", "fx": "bubble|meteor|gate_flash|confetti|smoke",
 "x": 56, "y": 39, "color": "green", "label": "+code"}

// alert card (top-bar bell + floating marker)
{"type": "alert", "level": "warn|crit",
 "code": "context_low|tests_red|laya_block|issue_stale",
 "msg": "...", "x": 0, "y": 0}

// a decision file appeared or resolved
{"type": "decision", "op": "created|answered", "id": "d123",
 "prompt": "...", "options": ["allow", "deny"], "timeout": 120}
```

### 2.2 Client to server

```jsonc
// unit/building order -> .devin/rts/intents/i<ts>.json (rts-intents.py
// surfaces it to the agent; world.py already projects kind:"order")
{"type": "order", "to": "c068a056|all",
 "order": "move|attack|stop|hold|patrol|set_rally|god_power",
 "x": 56, "y": 39, "power": "meteor",
 "quest": "07-session-worker", "id": "i<client-ts>", "queue": false}

// answer a pending gate -> decisions/<id>.json.response
{"type": "gate_answer", "id": "d123", "choice": 0, "text": "go"}

// control actions that run real bundle surfaces (allowlisted only)
{"type": "cmd", "cmd": "forge_ticket", "issue": 12}
{"type": "cmd", "cmd": "laya_guard", "state": {"body": "..."}}
{"type": "cmd", "cmd": "compact_hint"}            // surfaces a context alert
{"type": "cmd", "cmd": "refresh_repo"}            // force collector rescan

// client prefs + liveness
{"type": "set", "key": "theme", "value": "office|medieval"}
{"type": "ping"}
```

### 2.3 HTTP endpoints (all `127.0.0.1` only)

```
GET  /health                    {"ok": true}
GET  /snapshot                  same JSON as WS snapshot frame
GET  /telemetry                 collectors-only payload (repo.* block)
GET  /decisions                 pending decisions
POST /decisions/<id>/answer     {"choice","text"} -> response file
POST /intent                    validated intent -> .devin/rts/intents/
POST /cmd                       WS "cmd" equivalents (token-gated)
POST /event                     append to events.jsonl + world.apply + broadcast
GET  /ws                        upgrade
GET  /                          web/index.html + static assets
```

Compat: `POST /event`, `POST /intent`, `POST /decisions/<id>/answer` keep
rtsd semantics byte-for-byte so `rts-emit.py`, `rts-intents.py`,
`rts-decision.py`, and any rtsd client keep working if pointed at this port.

## 3. Command/intent lifecycle (the live contract)

The three intents surfaced into this session are the canonical example:

```json
{"kind": "order", "to": "all",      "order": "god_power", "power": "meteor", "id": "i1792852851616", "status": "surfaced"}
{"kind": "order", "to": "c068a056", "order": "attack", "x": 56, "y": 39, "quest": "07-session-worker",           "id": "i1792852866057", "status": "surfaced"}
{"kind": "order", "to": "8e0288ca", "order": "attack", "x": 52, "y": 39, "quest": "03-move-dirty-reconstruction", "id": "i1792852875999", "status": "surfaced"}
```

Lifecycle: UI POST writes `intents/i*.json` (`pending`), `rts-intents.py`
surfaces once (`surfaced`), `world.py` projects into the unit's order queue
(`_order_view` lifecycle), and the orchestrator decides execution (never
the UI).

Extended order vocabulary in v3: `dispatch` (spawn subagent, surfaced only,
never auto-run), `approve_gate` (shortcut for `gate_answer`), `compact`
(context-handoff request), `forge` (send ticket to planning desk).

## 4. Unit ECS state machine

Units are components over `world.py` hero/worker/minion records; the client
runs the animation FSM, the server owns truth.

```
States:  idle | move | work | attack | gate_wait | error | dead
Events:  order(move/attack) | arrive | tool_start | tool_end |
         decision_open | decision_close | test_fail | stale | despawn

idle  --order--> move --arrive--> work(tool_start)
work  --tool_end--> idle        work --emit--> bubble particles
work  --decision_open--> gate_wait --decision_close--> work|idle
any   --test_fail/exec_fail--> error --clear--> idle
any   --stale(600s)--> dead(fade)
attack = work on a contested/dirty tile (same strike anim;
       "attack" orders on quest coords light the tile contested)
```

Per-frame client sim: steering (seek/arrive + separation) over the tile grid
with A* pathfinding; spring-damper (Hooke, `x'' = -k(x-x0) - c*x'`) on
selection rings, camera, UI panels, and bubble rise.

## 5. Graphics pipeline (Three.js PBR)

- **Vendor**: single-file `three.module.js` pinned (r16x) under
  `web/vendor/`, fetched once by `bootstrap.py` (~1.2 MB, no CDN at runtime,
  ES-module + importmap, zero build step). `GLTFLoader` vendored alongside
  for optional `.glb` drops under `web/assets/`.
- **Materials**: `MeshStandardMaterial`/`MeshPhysicalMaterial` everywhere;
  procedural PBR maps generated on `<canvas>` (albedo value-noise, roughness
  variation, normal maps from Sobel of height noise, baked vertex AO on
  contact). No downloaded texture packs.
- **Lighting**: key `DirectionalLight` (sun/moon by day cycle + weather) +
  `PMREMGenerator` IBL from a procedural sky scene; warm point lights for
  forge fire / office lamps / monitor glow.
- **Shadows/AO**: `PCFSoftShadowMap`; SSAO via vendored addon passes if size
  allows, else cheap screen-space contact AO. Post budget <= 2 passes.
- **Tilt-shift/Bokeh**: custom tilt-shift shader pass (two-tap separable
  blur banded around the focus line), cheap maquete look, strength scales
  with zoom.
- **Particles**: instanced sprite pool for Tycoon bubbles (per-station
  emitter, color per 1.4, spring rise + wobble), GPU sparks for forge,
  meteor god-power projectile.
- **Geometry**: procedural composite meshes: keep/castle, towers, forge
  with animated shader fire, desks+monitors+kanban+coffee machine for
  office; units are articulated low-poly rigs (capsule skeletons, stride
  phase from velocity) until optional `.glb` assets exist.
- **Camera**: RTS orbital: pan (edge/WASD/MMB-drag), zoom-to-cursor wheel,
  rotate (Q/E or RMB-drag), isometric-locked default pitch around 50
  degrees, spring-smoothed; `F` frames selection, double-tap centers.
- **Selection**: raycast click + screen-space box select; ground marker +
  order flag; same right-click order grammar as v2.

## 6. HUD (per rts-hud-audio-design, three layers)

- **Top macro bar**: tokens/min (minerals), context % (vespene + low-gas
  warning crest), supply used/cap, dirty-file lumber count, idle-worker
  bell, weather/day orb, F10 menu, theme toggle.
- **Battlefield overlays**: hero roster F1-F5 (portrait, level, HP=context,
  MP=tokens-left), building strip, minimap (region + dirty-file heat),
  floating +resource numbers, decision cards over the gate tower.
- **Bottom console**: minimap, animated portrait, stats + 6-slot inventory,
  **4x3 command card** `QWER/ASDF/ZXCV`. Slots: Move, Stop, Hold, Patrol,
  Attack, Dispatch (hero-class picker), Forge, Guard (laya), Compact,
  Rally, Power (meteor), Menu. Each with SVG icon, hotkey badge, anchored
  tooltip naming the backing CLI surface.
- **Cafe-Mania rail**: issue tickets with SLA ring, drag to Forge.
- **Audio (optional, procedural WebAudio)**: reuse `app.js` DSP patterns;
  theme-aware foley (anvil clang vs mechanical keys; wind vs HVAC hum).

## 7. Backend design (`server.py`, stdlib only)

- `ThreadingHTTPServer` + vendored minimal RFC 6455 (same approach as
  rtsd: proven, zero-dep). FastAPI/websockets rejected: new deps need
  approval, no gain at a few clients (D2).
- `world_bridge.py`: `sys.path` import of `extensions/rtsd/world.py`;
  replay `events.jsonl` through `World.apply`, then file-tail the log
  (mtime poll, 0.5 s) for live events. Works whether rtsd is up or down.
- `collectors.py`: small functions returning dicts, each try/except +
  TTL-cached (git 5 s, issues 30 s, context 10 s):
  `git status --porcelain`, `git worktree list --porcelain`,
  `git branch --show-current`,
  `gh issue list --json number,title,labels,createdAt --limit 25`
  (skipped if `gh` absent), `.devin/scratch/optimized_ready.md` mtime,
  `.devin/ledgers/*.md` open-gate count, `bundle-models.json` context
  windows + chars/4 usage estimate, intents/decisions dir scans,
  load/CPU via stdlib fallbacks. All fail-open: missing tool means an
  empty section, never an exception.
- `POST /cmd` allowlist only: `forge_ticket` (writes a prompt-compiler spec
  JSON from the issue, runs `prompt_compiler.py --draft`), `laya_guard`
  (`laya_cli.py predict --preset guard`, subprocess JSON in/out),
  `compact_hint`, `refresh_repo`. **No arbitrary shell. No git mutations.**
  Anything order-like becomes an intent file for the orchestrator.
- Auth: per-boot bearer token (same as rtsd), `--remote` spectator token
  read-only; `--replay` mode reuses `World.apply` purity.
- `bootstrap.py`: creates `extensions/agent-rts/.venv`, installs
  `requirements.txt` (empty by default; optional extras commented),
  downloads pinned `three.module.js` + addons into `web/vendor/`
  (skipped when present or `--offline`).

## 8. Skill: `skills/agent-rts-commander/SKILL.md`

Global skill (manifest-tracked, per the spec path `skills/`). Contents:

- when-to-use: visualize/orchestrate the fleet, open the 3D dashboard.
- launch: `python extensions/agent-rts/bootstrap.py`, then
  `python extensions/agent-rts/server.py [--port 8798]` (auto-opens browser).
- telemetry contract: how the agent emits structured events
  (`POST /event` shape, parity with `rts-emit`) so bubbles/orders reflect
  each step; intent/decision file semantics.
- playbook: read snapshot, interpret gas/supply, act on surfaced order
  intents, answer decision gates, drag issue-to-forge mapping.
- pitfalls: never dispatch from UI, intents are advisory, fail-closed
  decisions.
`manifest.json` gains the `skills[]` entry + `skill_count` bump (audit gate).

## 9. Decisions register

| # | Decision | Rejected |
|---|---|---|
| D1 | Sibling extension sharing `.devin/rts/` + importing `world.py` | Forking world model (divergence); upstream-proxy to rtsd (needs 2 processes) |
| D2 | stdlib server + vendored WS; `.venv` exists but stays dep-free | FastAPI/uvicorn (new deps need approval, no benefit at this scale) |
| D3 | Vendored pinned `three.module.js`, zero build, procedural PBR textures | CDN (offline-unsafe), npm build (toolchain), texture packs (non-goal) |
| D4 | Repo telemetry in `collectors.py`, layered over snapshot; `World.apply` purity kept | Folding git/gh into world.py (breaks replay determinism) |
| D5 | `POST /cmd` allowlist; orders stay file-queue intents | Arbitrary command endpoint (security), UI-side dispatch (violates canon) |
| D6 | Port 8798, `AGENT_RTS_PORT` override | Sharing 8797 (collides with rtsd) |
| D7 | `skills/agent-rts-commander/` global + manifest entry | `.devin/skills/` (spec says `skills/`) |

## 10. File layout

```
extensions/agent-rts/
  bootstrap.py          # .venv + vendored three.js fetch
  server.py             # HTTP+WS daemon, rtsd-compatible endpoints
  world_bridge.py       # sys.path import world.py; tail events.jsonl
  collectors.py         # git/gh/.devin telemetry, TTL-cached, fail-open
  requirements.txt      # empty core (optional extras commented)
  selftest.py           # smoke: boot, /health, /snapshot schema, WS hello
  web/
    index.html
    vendor/             # three.module.js + addons (bootstrap-fetched)
    js/  main.js net.js scene.js camera.js themes.js buildings.js
         units.js particles.js selection.js hud.js pathing.js
         springs.js fx.js audio.js
```

## 11. Verification

- **Smoke (AC4)**: `python extensions/agent-rts/selftest.py` boots on an
  ephemeral port, asserts `/health`, `/snapshot` schema keys
  (`world,repo,decisions,intents`), `/telemetry` sections, WS upgrade +
  `hello` frame, static `index.html` 200, zero exceptions. Mirrors
  `rtsd/selftest.py` conventions.
- **Bundle gates before commit**: `python audit.py`, `python -m pytest`,
  exporter dry-run (skill manifest changed).
- **Manual**: browser console clean; both themes swap; an `exec` in a real
  session produces green bubbles at the Town Hall within one tick.

## 12. Phased build

- **Fase 1**: this document + WS/scene spec. Approval gate: paused here.
- **Fase 2**: `bootstrap.py`, `world_bridge.py`, `collectors.py`,
  `server.py` + `selftest.py` (headless-green before any 3D).
- **Fase 3**: `web/` scene/camera/selection/themes/particles/HUD;
  dual-theme swap; command card wiring to `/intent` + `/cmd`.
- **Fase 4**: `skills/agent-rts-commander/SKILL.md`, manifest sync,
  `audit.py` + `pytest` + exporter dry-run, launch command.
