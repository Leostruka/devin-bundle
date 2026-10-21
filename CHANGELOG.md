# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **rtsd procedural WebAudio DSP sound engine with Karplus-Strong, FM metallic clashes & theme-aware foley** (`extensions/rtsd/web/js/app.js`, #165): replaces basic single-oscillator beeps with a real-time WebAudio DSP synthesizer (`_getNoise` pink-weighted noise buffer, `_fm` inharmonic FM metallic partials, `_noise` biquad-filtered noise bursts, `_pluck` Karplus-Strong plucked string synthesis, and `syncAmbience` dual-filter continuous wind/rain soundscape tracking live `weather.wind_kph` and `weather.condition`). Adds distinct per-class and per-structure acoustic signatures (Runeforge anvil clang, Tavern lute chord, Altar cathedral choir triad, Marketplace coin chime, Portal void hum, Library crystal shimmer) and automatic Office Mode foley switching (mechanical key clacks, printer stepper whir, espresso steamer hiss, water-cooler bubble glug).
- **rtsd HUD architecture, F10 game menu, 4x3 QWER command card with vector icons & 6-slot inventory** (`extensions/rtsd/web/`, #164): `index.html`, `app.js`, and `engine.js` upgrade the bottom console to a competitive 4x3 (`Q W E R / A S D F / Z X C V`) Command Card with custom inline SVG vector icons (`ICON_SVG`) and an anchored WC3 Command Tooltip (`#cardtip`), add a WC3 6-Slot Runed Inventory Grid (`#invgrid`) and beveled HP/MP/XP progress bars (`#pbarHp`, `#pbarMp`, `#pbarXp`) beside the animated 3D portrait, add minimap filter toggles (`all`, `units`, `bld`) plus an isometric camera frustum polygon on the minimap in Office mode, and add the `F10` Game Menu modal (`#gamemenu`) featuring a full local weather forecast inspector and 1-click weather mode overrides.
- **rtsd 3D volumetric modeling, seamless terrain splatting, cast shadows & skeletal/Verlet physics** (`extensions/rtsd/web/js/`, #163): `theme.js` adds 3D PBR-inspired volumetric shading helpers (`_cylGrad`, `_sphereGrad`, `_roof3D` with sunlit West vs shadowed East slopes and shingle courses) and Ambient Occlusion contact shadows across all 11 structures and 22 unit/hero classes at `96x96` raster resolution. `engine.js` adds `_ensureTerrainCanvas` (offscreen organic biome splatting, stone-paved Keep courtyards, soft-edged wheel-rutted dirt roads, and sandy riverbanks), 2-wave Gerstner water superposition with specular glints, directional ground cast shadows, 4-node Verlet cloth capes trailing unit velocity and wind, 2-bone articulated leg stride kinematics, and ranged arrow/arcane projectiles during combat.
- **rtsd HUD, mechanics & gameplay overhaul + procedural soundscape** (`extensions/rtsd/web/`, #159): `index.html` and `app.js` add the WC3 Top-Left Hero Roster Bar (`#herobar`, click to select, double-click to center), AoE3 Top-Right Building Quick-Select Strip (`#bldbar`), live local Weather HUD orb (`#wxBtn`, showing city, temperature, condition, wind speed/direction, and 6h forecast tooltip, click to cycle weather modes), animated 3D-style Portrait canvas (`#portcv`), collapsible `Comms`/`Quests` drawers (`#togFeed`/`#togSide`), and floating hover tooltips (`#tooltip`). War Council (`#council`) no longer traps the viewport on expired decisions and gains a close button (`#councilClose`). The 3x4 Command Card (`#cmdcard`) adds icons, hotkey badges, `Gather` (`G`), and Building Commands when a structure is selected (1-click hero class recruitment at Barracks/Tavern, Town Bell, Rally, Tech Tree, Victory Score). Gameplay loops in `stepMotion` execute continuous Patrol (`P`), Gold/Lumber Gather hauling (`G` or right-click gold vein), Quest/Camp combat engagement (`A`), and visual AoE Spell effects (`pushFx`) backed by expanded procedural WebAudio SFX (`select_hero`, `select_bld`, `attack`, `gather`, `spell`, `thunder`, `bird`).
- **rtsd WC3/AoE3 unit, hero & building modeling + autonomous life** (`extensions/rtsd/web/js/`, #158): `theme.js` replaces basic disc/triangle/keep primitives with multi-part procedural silhouettes for all 22 unit/hero classes (pauldrons, class headgear, shields, broadswords/staves/bows/hammers, team trim) and all 11 structures (`town-hall` Keep with twin towers and oak gate, `barracks` with battlements and crossed spears, `tavern` with timber frame, chimney, and barrels, `library` with azure dome and lancet windows, `watchtower` spire, `runeforge` with glowing furnace and anvil, `vault`, `portal` with void vortex, `marketplace` with striped awnings, `altar` with winged statue, `trophy-hall` pantheon) plus `Theme.drawPortrait` for live animated portraits. `engine.js` adds `_drawBuildingAnim` (wind-flapping banners, drifting chimney/forge smoke, rising forge sparks, orbiting arcane rings, portal vortex, sacred braziers, watchtower beacon) and `_drawUnitLive` (WC3 Hero Glow, rotating Aura rune rings, wind-reactive flowing capes, striding boots + footstep dust puffs, `Stand - 1/2/3` look-around and weapon flourish fidgets, social nods between nearby idle allies, worker gold/timber hauling, and active combat/spell FX).
- **rtsd live local weather + wind physics + WC3/AoE3 terrain engine** (`extensions/rtsd/`, #157): `rtsd.py` adds `GET /weather`, `POST /weather` (mode cycling across `live`, `clear`, `overcast`, `rain`, `storm`, `snow`, `fog`, `windy`), and `snapshot.weather` backed by IP geolocation (`geojs.io`/`ipwho.is`) and Open-Meteo current + hourly forecasts cached in `.devin/rts/weather.json`. `sw.js` bypasses cache for `/weather`. `engine.js` and `theme.js` compute a unified wind vector (`wind_kph`, `wind_gust_kph`, `wind_deg`) that drives water wave crests, shoreline foam, swaying multi-layer forest trees, falling leaves, bending grass/reeds, cloud shadows, slanted rain/snow/fog particles, and storm lightning; terrain synthesis adds cobblestone Keep plazas, dirt roads connecting capitals and plots, river/lake channels with wooden bridges at road crossings, wandering critters, and dynamic Line-of-Sight vision around all allied buildings and units.
- **rtsd post-review audit fixes** (`extensions/rtsd/`, #155): resolved all 9 Spec and Standards findings from the v3.8.0 milestone review - `_apply_hook` now accepts `type == "hook.posttooluse"` alongside `hook == "PostToolUse"` for gold/burn/activity accounting; isometric wheel zoom projects `(p.x, p.y)` before updating `cam.x`/`cam.y`; `sw.js` bypasses cache for `/buildings`, `/score`, `/sessions`, and `/replay`; Marketplace merges `mcp_config.json`/`.devin/mcp_config.json` with `bundle-integrations.json` and reports tool counts; hero completion triggers `barkLine(cls, 2)` and minions group around their summoner hero; non-shift orders replace unconsumed orders (`stop` and debriefs mark orders consumed), waypoint lines chain `unit -> wp1 -> wp2`, and motion glides through queued waypoints in FIFO order; Office mode shows `OFFICE_BLD.label` in the building inspector, gathers idle heroes by the water cooler, and flashes printer fire on `runeforge` during breaches; `list_sessions()` caches replayed worlds by `(mtime, size)` and the Web UI Victory Screen renders Match History from `/sessions`; `<700px` mobile/PWA view gains `#mtabs` (`map | quests/econ | comms | orders`).
- **rtsd polish pass: animations, ambient life, day/night, guide card** (`extensions/rtsd/`, #136): unit animation states - heroes glide across the map toward their latest live order coordinate (display position eased per frame at a fixed walk speed, walk-bounce while moving) and drift back to their home tile when the queue empties; work-loop hammering while `status_live == "running"`, slow idle fidget otherwise; existing fade-outs kept for deaths/despawns. Ambient life (purely cosmetic, hash-seeded): birds crossing the battlefield sky plus drifting fog wisps, dust motes in the office theme; worker peasants still scurry on real hook firings. Day/night cycle: `world.started` (first event ts, replay-safe) anchors a 600s WC3-style day/dusk/night/dawn cycle; when enabled the map dims and building windows glow - toggled by the N key or the `day/night:` header button, persisted in `rtsd.daynight`, zero render cost while off. Hotkey audit + legend: the `?` guide card now lists every implemented binding - A attack-target, H hold, P patrol, `.` idle-worker cycle, F1-F4 camera bookmarks (Ctrl+Fn saves), plus the existing groups/Tab/SPACE/ESC/T/K/M/-/= set - an entity glossary, mode switches and mouse/command references (A took over from left-pan; arrows/edge/WSD still pan). Performance: procedural sprites are rasterized once per entry into offscreen canvases and blitted with `drawImage`, cutting per-frame path+text work for every unit/building/worker/fade.
- **rtsd replay + spectator + score screen** (`extensions/rtsd/`, #135): `rtsd.py --replay <events.jsonl>` runs a playback daemon that rebuilds the session deterministically through the same `World.apply` path; `GET /replay` reports `{total,index,playing,speed,done}` and `POST /replay` accepts `play`/`pause`/`seek` + `speed` (UI presets 1x/2x/4x, scrub slider = jump-to-event); each applied event broadcasts the identical upsert shape a live event produces, seeks rebuild via `World.replay` + a snapshot broadcast, and every other POST is denied server-side (403). Spectator mode: `--remote` now mints a second read-only token alongside the admin token (printed as a spectator URL, both stored operator-side in `.devin/rts/remote.json`); any client presenting it, loopback included, is scoped `client_role: "spectator"` in the snapshot and every POST returns 403, not just hidden in the UI - the web client additionally hides the command input/card under the spectator body class. Match history: `GET /sessions` walks `.devin/rts/` for every event log (`events.jsonl` plus archived copies like `sessions/*.jsonl`) and replays each through `World` for real per-session stats (events, agents, quests done/total, gates, tokens, duration). Score screen: `World.score()` aggregates quests/gates/heroes-by-xp/tokens/calls/duration over the same snapshot path, served at `GET /score`, shown as a victory-screen modal (auto-opens at end of a replay via a `score` WS frame) and as the TUI `/score` command. `tui.py` is now the command console: `--replay <file>` spawns the replay daemon and connects, `--spectate --token <t>` blocks `/intent`/`/answer` locally on top of server enforcement, and `/history` `/replay` `/play` `/pause` `/speed` `/seek` round out the console commands.
- **rtsd office mode: isometric theme** (`extensions/rtsd/web/js/`, #134): the office palette is now a true isometric presentation over the same world data. The engine centralizes projection in `toScreen`/`toWorld`: under `theme.iso` every world point maps through `(x - y, (x + y) / 2)` before the camera, and picking (`pickUnit`/`pickBuilding`/`unitsInBox`/`unitsInView`), order targeting, quest drops and pings all funnel through the same transform so the sprite you see is the sprite you click. Floor tiles render as iso diamonds (visible range derived by unprojecting the screen corners); camera clamp uses the projected map bounds; toggling re-centers on the same world point so the view never jumps. Office reskin table (GDD 3.2) covers all 11 buildings with interior glyphs + flavor labels: meeting room (town-hall), onboarding desk (barracks), break room (tavern), bookshelf (library), server rack (watchtower), printer (runeforge), whiteboard (vault), phone booth (portal), supply cabinet (marketplace), water cooler (altar), kanban wall (trophy-hall). Furniture and ambient life drawn from real positions only: desks under heroes with a typing bob while `status_live == "running"`, shared bench under minions, meeting table and water cooler at the town-hall plot, kanban walls behind quest markers. Decision summons: while a decision is pending, each hero gets a dashed walk line and a ghost sprite lerping toward a meeting-table slot (real unit positions, picking and selection untouched). Theme choice persists in localStorage (`rtsd.theme`). Minimap stays a top-down world overview (viewport rect skipped under iso).
- **rtsd alert system** (`extensions/rtsd/` + `web/`, #133): multi-tier alerts, all wired to real events. `world.breaches` in the snapshot lists every ledger with a failed gate, resolved to its territory (region named after the ledger, else the region holding a linked issue file's tile, else root) with the failed gate ids - so a wall breach keeps pulsing red across map and minimap until every gate in the ledger passes, and polling PWA/remote clients see the same alarm state without push infra. Snapshot diffs fire a new-breach alarm (horn, breach banner naming ledger+gates, fail ping at the region capital, `breach` feed line) and a `breach sealed` line when it clears. Procedural WebAudio signatures per tier (no asset files): council two-note sting on `decision.created`, low falling sawtooth horn on gate-fail/breach, soft sine blip on spawn pings, detuned-square clash on contested tiles, dual-triangle warn on upkeep escalations, quiet ack tick elsewhere. Sound controls: `snd:` header button / M key toggles mute, -/= set volume, both persisted in localStorage (`rtsd.snd`/`rtsd.vol`). Browser Notification API is opt-in via the `notify:` header button (permission-gated, graceful on deny/unsupported, fires only while the tab is hidden) for council calls, breaches and upkeep escalations. The alert stack orders by severity: red breach chips (`!region`, click = jump to the breached capital) outrank decision chips. TUI `/feed` prints `[ALERT decision]`/`[ALERT gate-fail]` lines for `decision.created` upserts and fail hints/debrief lines, and the hello snapshot now reports pending decisions plus active breaches.
- **rtsd tech tree + spellbook** (`extensions/rtsd/` + `web/`, #132): the K-key overlay renders the real skill economy. `world.tech` groups every `skills/<name>/` directory into the six GDD schools (Command/War/Lore/Craft/Creation/Summoning, plus `Unsorted` for skills the GDD table does not place) with a `path` back to its `SKILL.md`; `hook.posttooluse` events with `tool == "skill"` record casts in the event-sourced `world.skill_casts` ledger so cast spells glow with a count and never-cast skills render grey (availability + usage, never fake progression). Each hero carries a `spellbook` = the real skills literally named in its profile sheet (`agents/<profile>.md`), shown on the portrait, as `*skill` cast slots on the command card, and clickable in the overlay for the selected hero; casting posts a real `order` intent `{order:"cast", skill}` for `rts-intents.py`. Armory: `tech.armory` lists model tiers from `data/bundle-models.json` with the live subagent pin from `config.json agent.subagent_model` (falling back to the registry default); hero `model` now honors the profile's own `model:` frontmatter pin and `tier` is derived from that model's registry effort (medium=Footman, high=Commander, max=Knight), TOOLS-MAP as fallback. Library doctrines: `tech.doctrines` rates the 8 RAG chunking strategies (fixed/recursive/document/semantic/LLM/agentic/late/hierarchical) - `in_use` is set only when a real artifact proves it (cue-anchored whole-note retrieval in `scripts/memory-retrieval.py`/`memory-post-edit.py` over `.devin/memory/` notes marks `document`; `MOC.md` marks `hierarchical`), everything else shows not-in-use with empty evidence. Skill casts also emit `spell` feed lines and a spell ping on the library site, and `GET /buildings/library` returns `spellbook`/`doctrines`/`armory`.
- **rtsd economy HUD** (`extensions/rtsd/` + `web/`, #131): the top bar now reports a real income rate - `world.gold_log` records every PostToolUse event's est tokens (output chars / `CHARS_PER_TOKEN` + the same 200/call overhead used for gold, all replayed from `events.jsonl`) so `resources.income_min` is the trailing-60s token rate and `resources.income_last5` feeds a trend-bars sparkline in the new side Economy pane. That pane also shows the context window size and warn/crit/clear thresholds straight from `data/context-budget.json` (`resources.thresholds`) plus the supply split (`supply_heroes` / `supply_minions`). Per-hero economy: each unit's `burn` is the est token spend attributed to its event lane, and `turns_left` estimates remaining turns as (mana % of model window) / avg burn per call on that lane; heroes with no heartbeat report `null`, never a guess. Upkeep tier warnings: the HUD diffs successive snapshots and a tier crossing fires within one tick - econ feed line, res-bar flash animation, tone, and a minimap ping on the town hall (escalations only); upkeep itself stays derived from real context-pressure thresholds.
- **rtsd quest system** (`extensions/rtsd/` + `web/`, #130): the scratch-issue DAG is now a real WC3-style quest log. `world._quests` resolves dependency tokens to actual issue ids (short prefixes like `01` and GitHub-style `#120` both resolve; prose tokens stay visible in the chain text but do not block), recognizes the local `resolved` status, and enriches every side quest with `kind` (main/side), `done`/`failed`, `ledger` (per-issue ledger wins, else the effort ledger), gate tallies (`gates.pass/fail/total`), and `assignees` (heroes whose latest order carries the issue ref). Quest assignment: dragging a quest row onto a hero on the map or command-card/right-click Attack on a quest marker posts the same real `order` intent with the issue ref; the assigned hero's HP/xp/loot then track the issue's ledger gates and passed-gate `EVIDENCE` lines drop into the hero inventory tagged with the quest ref (WoW-style grid on portrait click, green-bordered quest loot). Map markers are state-aware: open `!` gold, blocked `?` greyed, failed `!` red until retried, done `*` rewards stamp. Comms feed gains `quest` lines: event-sourced `Quest accepted: <issue> -> <hero>` on assignment plus snapshot-derived `Objective complete (n/m)` / `Quest complete - reward: <ledger> ledger GREEN` / `Quest failed` lines (computed, never appended to `self.feed`, so replay stays pure). Quest log UI splits MAIN QUEST (latest `goal` intent) from SIDE QUESTS, greys blocked rows with the `a <- b` dependency chain, shows gate progress and assignee names; click a row to jump the camera to its marker.
- **rtsd war council** (`extensions/rtsd/` + `web/`, #129): `hook.permissionrequest` events now project into real pending decisions - the daemon writes `.devin/rts/decisions/<id>.json` in the exact shape `scripts/rts-decision.py --create` produces and appends a `decision.created` event (feed line names the requesting hero, gold minimap ping at town-hall). A decision poller in the tick also rings the bell for pending files created out-of-band (`rts-decision.py --create`), deduped via the event-sourced `world.dec_seen`. UI: pending decisions surface as a war-council modal showing the question, the requesting hero's portrait, council options with the last option marked as the deny-safe timeout default, and the rest of the queue stacked beneath; a header alert stack shows an `alerts:N` badge plus a flashing hero chip per pending decision (click pulls it to the chamber). Notification tiers per GDD: decision = modal + sound + gold ping, gate-fail = red breach banner + ping, info = feed only. Decisions stale past their `timeout` render as timed-out/deny-applied (fail-closed, matching `rts-decision.py --wait` semantics) and never re-alarm. Answers still flow through `POST /decisions/<id>/answer` writing the `.response` file `--wait` consumes; re-answer (409) and out-of-range choice (400) unchanged. Polling clients (PWA/remote) pick up new pending decisions via the snapshot diff the same way WS clients do.
- **rtsd comms feed** (`extensions/rtsd/world.py` + `rtsd.py` + `web/`, #128): the left Comms panel is now in-fiction radio chatter generated inside `World.apply` from real event payloads - hero deployments and debriefs (`read_subagent` returns report done/failed plus test counts parsed from the output), file-touch position updates naming the real path, war-council calls, order/goal/spawn intents, steering messages, raven deliveries, and agent status reports. Scrollback is event-sourced: `world.feed` rebuilds byte-identically from `events.jsonl` replay, and upsert broadcasts carry the new line (`feed` key) so live clients append without a refetch. A comms poller in the rtsd tick turns out-of-band surfaces into real events: new `.devin/mailboxes/*/inbox/msg-*.json` files append `mail.deposit` (deduped via `world.mail_seen`) and changed `status.json` notes append `agent.note`. Mailbox deposits fly a raven animation from sender to recipient on the canvas (arced path, flapping glyph, dotted trail) via a `hint` of kind `raven`. Feed UI: per-kind and per-class filter chips, click a line to select the speaking unit and jump the camera. `@unit text` in the command input resolves unit names (Knight-4) to the real agent id before posting the `message` intent for `rts-intents.py` mailbox delivery; plain text remains a goal intent.
- **rtsd orders queue** (`extensions/rtsd/world.py` + `web/js/`, #127): shift-click orders enqueue onto each hero's order queue (one `order` intent file per order, queue order preserved); queued waypoints render on the canvas as numbered flags with a dashed path from the unit, ghost (translucent) while the intent file is `pending` and solid once `rts-intents.py` surfaces it (queued/acknowledged/consumed state is overlaid at snapshot time from the real intent files). Right-click on the world canvas is a context order: snaps to quest POIs (attack with issue ref), buildings (garrison), or ground (move); with a building selected it sets that building's rally point (watchtower rally carries the target territory as alert channel). Barracks rally applies to the next spawned hero's lane server-side in `World._spawn_hero`. New `world.idle` snapshot list feeds an `idle:N` bottom-bar button that cycles and centers idle/stale heroes with no active order. Portrait panel shows the selected hero's live order queue.
- **rtsd selection + command card** (`extensions/rtsd/web/`, #126): box-drag multi-select with on-canvas rectangle overlay, shift-click toggle-add, double-click select-all-of-class-in-viewport, and Tab subgroup cycling. Control groups: Ctrl+0-9 assign, 0-9 recall, double-tap centers the camera on the group centroid; live group pips sit between portrait and card. Bottom-right command card (3-col grid) is generated per selected hero: Move/Stop/Hold/Patrol/Attack shared orders plus a per-class special (Far Seer Reveal, Knight Build, Cleric Verify, Ranger Track) and the full kit vocabulary (Cartography/Write/March/Farsight/Envoy/Parley/Camp) rendered enabled or disabled from the unit's real `kit` (agents/*.md allowed-tools). Move/Attack/Reveal arm a target mode resolved by the next map click; Attack snaps to quest POIs and embeds the issue ref in the intent. Every button posts a real `order` intent to `.devin/rts/intents/` via `POST /intent`; multi-select restricts to shared orders (move/stop) with one intent per unit; minimap right-click now orders the whole selection.
- **rtsd unit model** (`extensions/rtsd/world.py` + `web/js/`, #125): hero units now carry class identity derived from real profile data - `kit` (ability names mapped from the profile's actual allowed-tools in `agents/*.md`, `March` downgraded to `Verify` for read-only profiles, `Cartography` squire fallback) and `tier` (Footman/Knight parsed from the model column in `.devin/docs/TOOLS-MAP.md`). Hook firings become visible worker peasants that scurry between the last destination and the tool's building site (or the touched file's region capital), interpolated client-side off the server clock. Units bark: selecting shows the agent's real heartbeat `status.json` note when present, else a GDD class line; order intents show the ack line; done debriefs show the done line. Portraits show class, profile, tier, level badge, HP/mana, kit chips, and ledger loot. Failed heroes keep red outlines and fade out; low mana flashes the mana bar.
- **rtsd minimap + camera integration** (`extensions/rtsd/`, #124): every upsert broadcast now carries a world-derived `hint` (`{kind, xy}`) - file touches ping their tile (or `contested` once a second lane has touched it), spawns ping the hero's lane capital, failed debriefs ping red, `decision.created` pings gold at town-hall. The client keeps a ping queue: expanding rings on the main canvas, blinking blips on the minimap (click ping = jump camera), and SPACE cycles the last 8 alerts Warcraft-style. Minimap now draws building squares, ping blips, and per-lane territory tint (region `owner` = dominant lane). Minimap right-click issues a real `order` intent (`POST /intent`, kind whitelist extended) for the selected unit.
- **rtsd buildings** (`extensions/rtsd/world.py` + `rtsd.py` + `web/js/app.js`, #123): the 11 GDD structures are pinned to fixed map plots (affinity regions - town-hall/watchtower at `root`, library/trophy-hall at `.devin`, barracks/tavern at `agents`, runeforge at `scripts`, vault at `docs`, portal/marketplace at `extensions`, altar at `tests`; deterministic round-robin fallback when a region or plot is missing). New `GET /buildings/<id>` returns live per-building state: town-hall (goal, quest tallies, worker counts, pending decisions), barracks (hero-class table + pending spawn intents), tavern (real roster from `agents/` + `.devin/agents/` with model tiers parsed from TOOLS-MAP), library (actual `.devin/memory/` entries), watchtower (ledger pass/fail/pending + heartbeat count), runeforge (prompt/forge scripts on disk), vault (`git log --oneline -10`), portal (remote listener port/ttl/token-set), marketplace (`data/bundle-integrations.json` MCP servers), altar (failed heroes), trophy-hall (ledger evidence loot). Buildings are clickable on the map; the inspector offers real actions only - barracks class picker seeds `/spawn <profile>` intents, altar revive re-issues a spawn intent.
- **rtsd world map** (`extensions/rtsd/world.py`, #122): authoritative server-side tilemap; top-level dirs become named territories (weighted-Voronoi around deterministic ring capitals, bigger dirs = bigger territory), 2 fixed BFME-style build plots per region, per-tile fog of war (shroud/explored/lit; file-touch events light a 3x3 patch that re-dims after 180s, home territory starts explored), contested tiles when >1 lane touches a file, and POIs (quest markers from issue files, gold nodes from largest files, creep camps on untouched dirs). Layout persists to `.devin/rts/map.json` keyed by region signature and regenerates when top-level dirs change; fog demotions ride the 2s tick broadcast (`_map.fog` deltas). Renderer consumes the server map (`tile_region`/`fog`/`mark`/`pois`); client Voronoi is now demo-mode fallback only.
- **rtsd renderer v2** (`extensions/rtsd/web/`, #121): canvas-2D tilemap engine (`js/engine.js`) with camera pan/zoom (WASD, arrows, edge-pan, wheel-to-cursor, alt-drag), minimap canvas with viewport rect + click-to-jump, theme system (`js/theme.js`: battlefield + office palettes/glyphs with a sprite-sheet contract so real art drops in without code changes), and a rewired `js/app.js` consuming the v2 world snapshot (unit positions via deterministic hash placement, region Voronoi tilemap, contested-region tinting, war-council modal, `?bench` mode + live fps meter). OFFLINE DEMO mode when the daemon is unreachable. rtsd now serves any safe path under `web/` (traversal-guarded) so JS modules load; sw.js bumped to `rtsd-v2` caching the new shell.
- **rtsd world engine** (`extensions/rtsd/world.py`, #120): event-sourced v2 world model next to the v1 projection: units (heroes per GDD class table, exec-shell minions with TTL, hook-firing workers), 11 GDD buildings with activity counters, resources (gold=est tokens, lumber=context %, supply=live heroes, upkeep tiers from `data/context-budget.json`), quests (scratch-issue DAG + `/goal` main quest), map regions with reveal/contested tracking. All time-derived state computed at `snapshot(now)` so `events.jsonl` replay is byte-identical; daemon replays the log at startup; 2s tick thread broadcasts status deltas (running->idle->stale decay, minion expiry). `/snapshot` gains `v:2` + `world` key; v1 keys unchanged.
- **AgentCraft RTS v2 GDD** (`.devin/scratch/agentcraft-rts-v2/gdd.md`, #119): metaphor bible for the v3.8.0 RTS milestone; entity mapping tables covering all bundle surfaces (13+2+4 agent profiles as hero classes, 83 skills as spells in 6 schools, 35 scripts as workers, 22 extensions as allied arsenal, 28 runtime tools, 8 hook events), mechanics mapping (HP/mana/supply/gold/lumber/upkeep/fog/quests/loot/barks to real data sources), dual-mode spec (battlefield + office themes on one engine), desktop + PWA layout wireframes, programmer-art direction, per-class voice lines, and binding honesty rules.

## [3.7.0] - 2026-10-18

### Added

- **`extensions/rtsd` RTS overlay**: local state daemon projecting ephemeral `run_subagent` activity into a live RTS-style view (AgentCraft-inspired heroes/quest board/decision podium/evidence panel). Python stdlib only — HTTP + hand-rolled RFC 6455 WebSocket (snapshot + upserts), fleet/ledger/intent/decision file projections under `.devin/rts/`, canvas-2D web UI, PWA (manifest + service worker + mobile tabs), stdlib TUI client (`/status /agents /decisions /answer /feed`), `--remote MIN` LAN listener with per-session token + TTL deny-safe expiry + auth audit events.
- **RTS bridges in `scripts/`**: `rts-emit.py` (fail-open lifecycle event tap wired into the `_hookrun` chains), `rts-intents.py` (UserPromptSubmit surfacing of pending UI intents + mailbox deposits with traversal guards), `rts-decision.py` (create/wait bridge for the podium, fail-closed on timeout).
- **Heartbeat clause** in `skills/project-orchestrator/templates/delegation-contract.md`: workers write `.devin/rts/agents/<Contract ID>/status.json` per milestone; rtsd attaches heartbeat to the hero by contract-id.

### Fixed

- `extensions/computer-use` scoped channels: `_scoped_mouse`/`_scoped_type` gated on `cm.get_profile()` which resolves env + persisted profile file — an ambient `human`/`smooth` preference silently blocked every scoped dispatch (exit 2) even without `--profile`. Gate now fires only on an explicit `--profile human/smooth` flag, matching `cu_scope.resolve_channel`. Fixes `test_cu_scope_boundaries` (3) + `test_uia_has_no_key_concept`.
- `audit.py`: compile step wrote bytecode (`py_compile`) then warned about the `__pycache__` dirs it created itself — an always-firing warning. Compile now uses the `compile()` builtin (no writes); the `__pycache__` check matches its stated intent (tracked files via `git ls-files`).
- `devin-session-launcher.ps1`: session picker now lists only sessions of the current directory. `Get-DevinSessionData` discards a shared `DEVIN_N_SESSIONS_FILE` cache whose entries all belong to another `working_directory` (multi-project mode: parent cache is cwd-scoped to the parent) and refetches live; `Start-DevinSession` filters parsed sessions by `working_directory` as a safety net. 2 new Pester tests (26 total).

### Changed

- **Devin CLI alignment `3000.11.92`**: `validated_cli_version` bumped from `3000.11.1`; new `3000.11.92` capability-decision table in `DEVIN-CLI-COMPATIBILITY.md` covering `3000.11.3`→`3000.11.92`. Adopted `agent.subagent_model: swe-2-max` in `config.json` (verified empirically: `subagent_explore` ran on SWE-2 Max with the key vs parent-inherited SWE-2 High without). Documented `PreCompact`/`PostCompact` events, `/goal`, steering, `/billing`, `Alt+Enter` session model pick, `devin connect`/`cloud drs`, plugin `platforms`/`PLUGIN_ROOT`/`PLUGIN_DATA`, `sandbox.excluded.allow`, and rules/`read_config_from` hardening fixes.
- `TOOLS-MAP.md`: new commands (`/goal`, `/billing`, `Alt+Enter`, `devin connect`, `devin cloud drs`); unused hook events list now includes `PreCompact`/`PostCompact`.
- Plan: `.devin/plans/2026-10-15-adequacao-devin-cli-3000.11.92.md`.

## [3.5.0] - 2026-10-10

### Added

- **`laya-compactor` Smart Window pruning** (`extensions/laya-compactor/`): per-item transcript compaction through the resident Laya worker — `compact-item-v1` keep/truncate/drop decision profile (suggestion-only), tool_use/tool_result pair integrity, orphan-risk abort, reduction-floor fallback returning the original transcript.
- **`image-forensics` extension + skill** (`extensions/image-forensics/`): metadata inspection + PRNU residual/PCE scoring emitting `real_capture`/`synthetic`/`inconclusive` verdicts with confidence; abstains on weak residual or recompression.
- **`craft-bridge` extension** (`extensions/craft-bridge/`): uniform dispatch over the verified storytold suite (filmcraft, photocraft, vectorcraft, wordcraft, pdfcraft, gridcraft, deckcraft, cadcraft, lightcraft, soundcraft — Apache-2.0; spark MIT), cross-engine scene manifest, ops matrix, and a static `spark-view` gsplat preview page.
- **`animation-direction` pipeline**: local ASR timestamped transcript (`extensions/asr/`), motion scene manifest with mandatory approval gate (`extensions/remotion-render/plan_check.py` validates timing/overlap/read-time/budget), Remotion rendering + FFmpeg compositing.
- **`ppisp-prep` extension** (`extensions/ppisp-prep/`): photometric QC (exposure/WB/vignetting variance) emitting go/correct/recapture, wrapping NVIDIA PPISP upstream rather than reimplementing.
- **`learn-mode` skill**: opt-in learning-first collaboration adapted from `nykooi1/vibe-wise` — user owns design decisions, agent explains concepts, waits for approval before implementing, explains the diff.
- **Pocock upstream ports** (`mattpocock/skills` @49dd158): `skills/pr` (visual Summary + Evidence + Merge Danger), `skills/retro` (session retrospective feeding `continuous-improvement`), `skills/setup-pre-commit` adopted into the repo; 22 skills verified already covered, 12 skipped with reasons in `.devin/research/pocock_port_matrix.md`.
- **`computer-use` screen recording** (`extensions/computer-use/record.py`): duration-based capture to mp4/webm via streamed ffmpeg rawvideo pipe (honest exit-2 when ffmpeg is absent) or animated webp/gif via the bundled Pillow dep; every run also writes a reservoir-sampled contact-sheet PNG that agents can `read` directly. Absolute-deadline pacing reports `dropped`/`fps_actual`; `--env` records isolated guests via `backend.observe()`.
- **`project-bootstrap` rule templates** — `templates/domain-rules.md` (glob-scoped to domain paths, for business rules) and `templates/devin-config-rules.md` (scoped to `.devin/**`, teaches bundle conventions). Frontmatter format verified on CLI 3000.11.1 (`trigger: glob`, `globs:` YAML sequence).
- **`prompt_compiler.py` Golden Template refactor** — the script no longer guesses: it validates and assembles a strict spec (`effort`, `persona`, `goal`, `context`, `acceptance[]`, `in_scope[]`, `out_scope[]`, `phases[]`) drafted by the agent. Effort/persona are semantic agent decisions (language-agnostic); `--draft <file|->`/`--spec` input; `recommended_model` resolves family+effort via `bundle-models.json` deterministically. `prompt-compiler` skill rewritten around the agent-as-Prompt-Engineer flow.
- **Pester suite for the devin-N launcher** (`tests/pester/`): AST-based `Import-DevinFunctions` loads real functions from `devin-N.ps1`/`devin-session-launcher.ps1` without executing the interactive wizard; 24 tests cover fuzzy matching, quote escaping, EncodedCommand round-trip, runspace spinner (incl. `$Ctx` argument passing and nested-hashtable integrity), shared `devin ls` cache and path-suggestion TTL.
- **ADR 004** (`.devin/adr/004-tui-manual-devin-launcher.md`): records the decision to keep the manual TUI in the devin launcher (Terminal.Gui v2 API churn and pwsh gaps; ConsoleGuiTools archived).
- **`devin-N` README section** documenting the multi-instance launcher usage.

### Changed

- **Devin CLI alignment `3000.11.1`**: `validated_cli_version` bumped from `3000.10.27`; new `3000.11.x` capability-decision table in `DEVIN-CLI-COMPATIBILITY.md` covering `3000.10.31`→`3000.11.1` (recursive `.devin/rules/` discovery, `allowed-tools` write grant, subagent always-on rule inheritance, cloud commands, `otel` block, `Exec` deny precedence). All verified empirically on the installed CLI.
- `.devin/rules/README.md` moved to `.devin/docs/RULES-DIRECTORY.md` — recursive rule discovery listed it as a `manual` rule.
- Duplicate `3000.10.x capabilities` / `read_config_from` sections in `DEVIN-CLI-COMPATIBILITY.md` consolidated.
- `TOOLS-MAP.md` documents the `3000.11.1` cloud commands (`--cloud`, `/handoff`, `/pickup`, `ssh`).

### Fixed

- `install.ps1`/`install.sh` now create the `.venv` for `scrape-tools` (previously `computer-use` only) - the skill's documented interpreter path was never provisioned.
- `manifest.json` `export_hash` drift for `memory-stop.py`/`spec-consistency.py` corrected.
- **`devin-N.ps1` audit remediation** (13 confirmed defects): original branch restored in every mode incl. multi-run non-worktree children; `git status --porcelain` gate before any `worktree remove --force` with dirty-file listing and confirm; stale-worktree sweep scoped to the launching session via `worktree lock` + `.session-<pid>` markers; single-quote escaping in `Get-InstanceCommand` and uniform `-EncodedCommand`; `status --porcelain --untracked-files=no` in the pull gate covers staged changes; branch-list `-like` patterns escaped via `[WildcardPattern]`; impossible `[Nova branch]` sentinel replaces collidable `devin-new`; `$windowSize` initialized before the key-drain loop; dead `'0'` shortcut branch removed; `NaoGitRepo` template gained its `{0}` placeholder; top-level `param()` accepts `%*` args with a warning instead of silently ignoring them.
- **`Invoke-WithSpinner` now uses a `[powershell]::Create()` runspace** instead of `Start-Job`: no child pwsh process, no CliXml degradation (nested hashtables survive), `$Ctx` hashtable parameter passing replaces `$using:`; all 9 call sites updated.
- **Windows Terminal window targeting without process-diff**: new windows are spawned with `wt -w <unique-id>`, children set a `[Console]::Title` marker, hwnd is resolved via `EnumWindows` title match, and cleanup sends `WM_CLOSE` only to windows created by the session (no more `Stop-Process` on foreign `WindowsTerminal` processes).
- **UX/perf**: dependency preflight (`git`/`devin` fail-fast, `gh` warnings); single `%(upstream:track)` call for ahead/behind (per-branch `rev-list` only as fallback); spinner around serial `gh` metadata calls; 500ms TTL cache for path suggestions; `devin ls` shared with children via `DEVIN_N_SESSIONS_FILE`; `TreatControlCAsInput` in the path editor; 3s fixed sleep replaced by a bounded child-liveness probe; `Esc` on the summary screen reconfigures any project; launcher literals centralized in `$LM`.
- **Empty `catch {}` blocks** removed across both scripts (now log via `Write-Verbose`).

## [3.4.0] - 2026-09-21

### Added

- **`teach` skill** — stateful tutoring engine with ZPD-strict gating and state integrity checks.
- **`prompt compiler` + `/prompt` skill** — compile rough intent into structured prompts (`ai-tools`).
- **`diagram-tools` extension + `architecture-diagrams` skill** — PlantUML serverless renderer.
- **`media-tools` skill** — routes the visual-FX extension (grainrad parity).
- **`laya-tools` extension + `implement-laya` skill** — wrapper for the laya decision engine; bilingual EN/PT routing.
- **`spline-operator` extension + `operate-spline` skill** — Spline MCP bridge control (`ws://127.0.0.1:19692`), 36 tools, daemon keeper, `3d_load_skill` protocol.
- **`creative-engineering` skill + aesthetics KB** — 15 visual archetypes under `extensions/media-tools/knowledge_bases/aesthetics/` (CRT, receipt, depth-map, blob, datamosh, 1-bit dither, night-vision, brutalism, PC-98, wired-cyber-UI, constructivism, Y2K, PSX, risograph, vaporwave) with math/algorithm + Python + Web implementations per archetype.
- **`creative_tooooools.json`** — scraped tooooools.app catalog (16 tools) + refreshable stdlib scraper `update_tooooools_db.py`.
- **`NOTICE.md`** — third-party attributions (impeccable Apache-2.0 chain, MIT/conceptual sources, runtime deps).
- **Release automation CI** — tag-push workflow verifying manifest/CHANGELOG sync.

### Changed

- **Ecosystem alignment refactor** — routing sharpened (ask-bundle/planning/intake/execution/memory boundaries), 8 cross-skill wires added, `obsidian-workflow` split 70KB→3.3KB index + 4 deferred `modes/`, loose scripts moved to `scripts/`.
- README/LICENSE placeholders rendered for the concrete repo identity.

### Fixed

- `validate_mermaid.py` canonical path resolution (fell back to global path).
- Manifest mojibake (`â€”`/`→` double-encoding) reverted to UTF-8.
- `test_recv_collects` macOS flake — root-caused: bare `recv_from` raced the drain thread; now polls with `wait=`.

## [3.3.0] - 2026-09-20

### Added

- **`system-control` extension** — authorized OS-level control: typed contract v1, deny-wins policy with one-shot request-bound confirmations, bounded argv-only execution, persistent owned sessions (loopback JSONL daemon), resumable event streams, root-bound hash-verified file ops, native Windows (Job Objects/SCM/WMI), Linux (procfs/pidfd) and macOS (ps/kqueue) adapters, opt-in privileged broker seam (JEA/polkit templates), benchmark harness (decision: stay_python), thin skill router + USAGE docs.
- **`scan` skill** — goal-driven codebase investigation via Plan→Shard→Map→Reduce orchestration (`/scan` equivalent).
- **`ai-tools` extension** — offline-first ML tooling with abliterator PoC.
- **`brag` skill** — launch-video generation via Hyperframes.
- **`media-tools`** — grainrad.com parity: 15 effects, pipeline, presets, animated io.
- **`computer-use` terminal control** — bound read/control for WT/conhost/mintty, WinPTY PTY spawn via pywinpty, sentinel-gated exec.
- **`computer-use` browser** — bound-browser observation + full-fidelity event daemon (network, dialogs, HAR-lite).
- **`computer-use` mintty OCR** — text read via Windows.Media.Ocr (winrt).
- `computer-use` action profiles, observation contracts, dual-engine browser client.

### Changed

- **Bundle slim** — hooks 22→9 bindings, skills 83→48, AGENTS.md 18→11 KB, native Devin CLI capabilities adopted.
- Layout refactor — `docs/` dissolved into `.devin/`; plugin manifest dropped.
- README — skill groups deduplicated, counts fixed, extensions layer documented.
- `context-hygiene` — code-minification caution note (real but completion-scoped).
- Registry trimmed to SWE-2-only models.

### Fixed

- `computer-use` — phantom context menus from emergency_release; SM_SWAPBUTTON button translation; JSON stdout guard; UIA segfault.
- `devin-N` — orphan worktree dirs and reserved-name files; worktree branches preserved and re-attached; strict-mode sessions tolerated.

## [3.1.1] - 2026-09-08

### Fixed

- Resolved all remaining minor audit findings from `AUDIT_REPORT.md` in seven batches (lotes 1-7).
- `audit.py`: 32/32 checks pass, 0 errors.
- `python -m pytest -q`: 289 tests pass.
- Live installation synchronized with bundle after all changes.

## [3.1.0] - 2026-09-06

### Added

- **6 new skills** for governance, security, and cost control:
  - `ontology-validator` — validate structured knowledge and ontology integrity.
  - `task-sizer` — estimate and calibrate task scope before dispatching.
  - `secure-defaults-check` — pre-commit/pre-push security defaults verification.
  - `agent-cost-guard` — guardrails for token and parallel-tool cost.
  - `intention-capture` — capture and pin user intent before implementation.
  - `api-context-spec` — design and validate API context contracts.
- Validated task-adaptive harness recipes, durable session logging, MCP code-mode routing, model-interface preflight, bidirectional patch verification, temporal regression checks, and prompt-bloat quality gates.
- Validation coverage for Leo's orchestration contract.

### Changed

- **`leo` skill**: promoted from session-start router to the bundle's universal orchestrator, with direct routing to `wayfinder` and specialist domains, multi-skill composition, and control returning to Leo until verified completion.
- Live bundle installation and audit now validate all 32 checks with no warnings.

## [2.9.0] - 2026-09-01

### Added

- **7 Matt Pocock AI Coding workshop plans**: skills, plans and ledgers for context-workflow, grill-me, prd-to-issues, afk-loop, tdd-feedback, deep-modules, and push-pull-review.
  - `context-window-hygiene` + `scripts/context-budget.py`: added `SMART_ZONE_TOKENS` (100k), `--simulate`, and explicit `clear` over `compact` nudge.
  - `grilling`: assertive questions, one recommendation alongside every question, and `shared design concept` PRD export.
  - `planning-pipeline` and `writing-plans`: PRD as destination document, declared modules and interfaces, tracer-bullet vertical slices, and prototype/disposable asset lifecycle.
  - `afk-loop`: new skill for unattended TDD over local Markdown issues in isolated worktrees.
  - `tdd`: RED→verify RED→GREEN→verify GREEN→REFLECT→REFACTOR contract, anti-cheat reflection, and `Feedback Loops Are the Quality Ceiling`.
  - `improve-codebase-architecture`: Ousterhout deep vs shallow module heuristics and five deepening refactor moves.
  - `code-review`, `receiving-code-review`, `impeccable`: push/pull pattern distinction with Sand Castle as mental model, no Docker dependency.
- **`afk-loop` skill** — Prompt/workflow for an unattended agent that consumes local Markdown issue files under `.devin/scratch/<feature>/issues/*.md`, uses TDD in an isolated git worktree, and picks the next ready issue autonomously from a DAG of blocking relationships. Stops when no ready issues remain or on blockers; does not commit/push to `main` without human confirmation and does not require Docker.
- **`youtube-fetcher` skill** — Devin-native, stdlib-first, network-free adapter for turning a YouTube URL and provider/fixture caption/metadata JSON into raw, timestamped transcript + metadata Markdown under `.devin/notes/youtube/`. Strict host allowlist for URL validation, input/output size limits, symlink containment, duplicate preservation, and handoff to `structured-knowledge-extraction`. Conceptually adapted from JimmySadek/youtube-fetcher-to-markdown (MIT); no code copied.
- **`leo` skill** — `/leo` session-start skill that injects bundle operating rules, skill discovery, tool verification, telegraphic output, subagent/model routing, and a clear priority hierarchy. Replaces the playbook experiment.

### Changed

- **README.md**: complete rewrite explaining the full ecosystem (rules, skills, agents, tools, hooks, context, memory) and operational flows (idea → ship, AFK loop, deep modules, push/pull review). Updated counts and badges.
- **manifest.json**: version `2.8.1` → `2.9.0`, skill count `75` → `76` with `afk-loop`.
- **docs/TOOLS-MAP.md**, **docs/DEVIN-CLI-COMPATIBILITY.md**: skill count updated to `76`.

## [2.8.1] - 2026-08-29

### Fixed

- **README.md**: corrected rule count (19 → 20), script count in Mermaid (13 → 17), added `context-pressure.py` and `SessionEnd`/`memory-stop.py` rows, clarified `credentials.toml` as generated.
- **docs/TOOLS-MAP.md**: added `context-pressure.py` (PostToolUse) and `SessionEnd`/`memory-stop.py` rows; updated rule count (19 → 20); corrected claim that `SessionEnd` was unused.
- **docs/SKILL-TIERS.md**: added `youtube-fetcher` to Data tier.
- **CONTRIBUTING.md**: corrected hook exit code (1 → 2) for block.
- **SECURITY.md**: updated `post-compaction-reminder.py` → `constraint-pinning.py` and `refine` skill → `primeagent-reference` Refine mode.
- **hooks.v1.json** (root + `.devin/`): synchronized with `config.json` hooks; uses `python scripts/*.py` paths and lists all 8 lifecycle events.
- **manifest.json**: synchronized `impeccable` purpose with `SKILL.md` description.

### Changed

- **12 skills**: removed YAML quote wrapping from `description` frontmatter so `validate-skill-format.py` scores 100 (`a11y-audit`, `api-design`, `cost-optimization`, `database`, `deploy`, `docker`, `e2e-testing`, `i18n`, `impeccable`, `legacy-refactor`, `performance`, `security-audit`).

## [2.8.0] - 2026-08-28

### Added

- **11 new skills for modern agent coverage**:
  - `deploy` — deploy, release, rollback, and smoke-test workflows.
  - `security-audit` — defensive SAST, dependency CVE, and secret-leak scanning.
  - `performance` — profiling, benchmarking, and bottleneck optimization.
  - `a11y-audit` — WCAG, keyboard, screen-reader, and contrast checks.
  - `api-design` — REST/OpenAPI design and contract testing.
  - `database` — schema design, migrations, query review, and indexing.
  - `e2e-testing` — Playwright/Selenium/Cypress critical-journey tests.
  - `cost-optimization` — token, cache, model routing, and MCP cost reduction.
  - `docker` — container build, run, compose, and image scanning.
  - `i18n` — internationalization, pluralization, LTR/RTL, and formatting.
  - `legacy-refactor` — strangler-fig, seams, and incremental modernization.

### Changed

- **manifest.json**: version 2.7.0 → 2.8.0, 71 skill entries.
- **README.md**: skills badge 60 → 71, version badge 2.7.0 → 2.8.0, summary and Mermaid diagram updated.
- **docs/TOOLS-MAP.md**: skills count 60 → 71.
- **docs/SKILL-TIERS.md**: new "Infra / Quality / Release" tier with the 11 new skills.

## [2.7.0] - 2026-08-27

### Added

- **project-setup skill**: FASE 0 deep research + 10-step setup loop for bootstrapping `.devin/` configuration in projects.
- **Cross-skill wiring**: `context7`, `deep-mode`, and `research` wired into 35+ skills where library docs, unfamiliar code, or primary-source investigation is needed.
- **Engineering skill integration in `project-setup`**: Passo 4.5 now explicitly runs `grilling`, `domain-modeling`, `project-memory`, `triage`, and `planning-pipeline` to populate the project's knowledge base before work begins.

### Changed

- **Agent-produced artifact paths**: `docs/specs/` → `.devin/specs/`, `docs/plans/` → `.devin/plans/`, `docs/obsidian/` → `.devin/obsidian/` (with legacy fallback) in `grilling`, `writing-plans`, `dispatching-parallel-agents`, `code-review`, and `obsidian-workflow`.
- **manifest.json**, **README.md**, **audit.py**: version bumped to 2.7.0.

## [2.6.0] - 2026-08-27

### Added

- **project-memory skill**: captures project-specific knowledge as plain-text
  Markdown notes under `.devin/memory/`, with user approval, cue-anchored
  frontmatter, and Obsidian-compatible wikilinks.
- **Memory helper scripts**: `capture-memory.py`, `query-memory.py`, and
  `audit-memory.py` for note lifecycle and link/orphan validation.
- **Cue-anchored memory hooks** (arXiv:2607.20972, arXiv:2608.15008):
  - `memory-retrieval.py` on `UserPromptSubmit` (keyword cues)
  - `memory-post-edit.py` on `PostToolUse` `write`/`edit` (path cues)
  - `memory-post-exec.py` on `PostToolUse` `exec` (symbol/keyword cues)
  - `memory-stop.py` on `Stop` (session review nudge)
- **Rule 21**: "Don't think through uncertainty — research or ask".

### Changed

- `manifest.json`, `README.md`, `docs/TOOLS-MAP.md`, `audit.py`: updated
  script counts to 17, hook script counts to 15.
- `docs/MODEL-GUIDE.md`: added arXiv:2607.20972 and arXiv:2608.15008 to the
  source verification table.

## [2.5.3] - 2026-08-26

### Fixed

- `audit.py`: removed hardcoded version and badge checks, using manifest and runtime counts.

## [2.5.2] - 2026-08-26

### Added (iter 8.5 — continuous improvement + mermaid + cleanup)

- **continuous-improvement skill**: FASE 0 deep research + 10-step self-improvement
  loop based on Constitutional AI, RISE, Six-Step Reframing, and held-out
  validation. Enforces the full directive and prevents skipped steps.
- **PermissionRequest and SessionEnd hook events**: added to `config.json` and
  `hooks.v1.json` to match all 8 Devin CLI lifecycle events. Audit check [30]
  prevents future drift.
- **Mermaid architecture diagram in README.md**: replaced ASCII diagram with
  a `flowchart TB` Mermaid block, validated by `validate-mermaid.py`.

### Changed

- **README.md and SKILL-TIERS.md**: skill count 49 → 50, added
  `continuous-improvement` to skill inventory and tier list.
- **scripts/validate-skill-format.py**: default scan now includes bundle root
  `skills/` as the source of truth, plus project `.devin/skills/` and global
  installs.
- **TOOLS-MAP.md and audit.py**: updated skill count checks 49 → 50.

### Removed

- **ci-logs.zip**, `__pycache__/`, `.pytest_cache/`: cleaned project junk.

### Added (iter 8.1 — CLI replicas of cloud-only features)

- **deep-mode skill**: replicates Ask Devin's Deep Mode (`!deep` in
  Slack/Teams) for the CLI. Multi-pass agentic search (broad sweep ->
  deep read -> cross-file synthesis -> architecture map) with
  mandatory file:line citations. Sources: docs.devin.ai/work-with-devin/ask-devin,
  docs.devin.ai/integrations/slack, cognition.ai/blog/new-self-serve-plans-for-devin.
- **data-analyst skill**: replicates Devin cloud's Data Analyst Agent
  (DANA) for the CLI. SQL-first exploration via MCP data sources,
  schema discovery + caching, query formulation, analysis, and
  matplotlib/seaborn-style visualizations. Read-only by design.
  Sources: docs.devin.ai/work-with-devin/data-analyst,
  docs.devin.ai/use-cases/gallery/dana-slack-data-analyst,
  docs.devin.ai/release-notes/2025.
- **playbook skill**: replicates Devin cloud's Playbook feature for
  the CLI. Structured prompt template (Procedure, Specifications,
  Advice, Forbidden Actions, Required from User), local library
  (`.devin/playbooks/*.devin.md`), macro approximation, create-from-
  session workflow. Sources: docs.devin.ai/product-guides/creating-playbooks,
  docs.devin.ai/product-guides/using-playbooks,
  docs.devin.ai/work-with-devin/advanced-capabilities.
- **obsidian-workflow skill enhanced**: 4 new steps (17-20) complementing
  existing rigor to match DeepWiki cloud. Effort levels (low/medium/high)
  in `wiki-config.json` controlling depth. Deep Research pass (Step 18)
  — architecture critique, anti-patterns, optimization opportunities,
  senior-reviewer-level analysis. TechDebt page (Step 19, `11-TechDebt.md`)
  — cited issues, numbered (AP-001/OPT-001), categorized. Conversational
  Q&A (Step 20) — `deep-mode` skill integration for multi-pass search
  over wiki with double citations (wiki + source). Backward compatible:
  absent `effort` defaults to `high` (existing behavior). Sources:
  docs.devin.ai/work-with-devin/deepwiki, cognition.com/blog/deepwiki,
  marktechpost.com/2025/04/27/devin-ai-introduces-deepwiki.
- **obsidian-workflow validators**: 2 new scripts + 1 updated.
  `validate_wiki_content.py` (9 content rigor checks: source path:line
  format, min 5 sources per page, Sources: footers, overview links to
  all root pages, function ## Links, source columns in tables, TechDebt
  content, architecture critique, effort valid). `find_orphan_pages.py`
  (graph orphan detection — referenced in checklist but did not exist).
  `validate_wiki_structure.py` updated with 3 new checks (effort valid,
  TechDebt exists, arch critique section). SKILL.md updated with
  validation scripts table and content rigor checklist item.
- **manifest.json scripts list**: added `scripts` array (was missing —
  `script_count: 12` but no list). 12 .py + 1 .js entry. audit.py check
  [9b] validates consistency (count match, disk existence). Check count
  23 -> 24.
- **Counts updated**: 46 -> 49 skills in README.md (summary, diagram,
  tree, badge), TOOLS-MAP.md, SKILL-TIERS.md (3 new entries in
  Pesquisa/Data/Planejamento sections), manifest.json (3 entries +
  skill_count 46->49), audit.py (checks [9] and [18]).

### Fixed (iter 8.3 — self-improvement loop: hook FP/FN fixes + audit hardening)

- **destructive-gate.py commit message parsing**: strip_commit_message()
  now extracts only the command portion before `-m`/`-F`/`--message`,
  preventing the gate from blocking descriptive commit messages that
  mention gate names. (ref-030)
- **check-ai-signature.py self-detection skip**: write/edit to
  check-ai-signature.py or validate-skill-format.py was blocked because
  the detector code contains the signature patterns. Added self-detection
  skip. Also fixed exec handler to extract `-m` message. (ref-031)
- **silent-error-review.py false positives**: bare exception-name regex
  matched past-tense fix descriptions ("the fix resolved the KeyError").
  Fixed: require colon after exception name or Traceback/raise prefix.
  (ref-032)
- **validate-refinement-evidence.py tool-call patterns**: flagged
  ref-002 as PHANTOM despite evidence containing write/edit/exec. Added
  write|edit|exec to REPRODUCIBLE_PATTERNS regex. (ref-033)
- **check-ai-signature.py allowed contexts**: "AI-assisted tooling"
  blocked descriptive documentation. Added ALLOWED_CONTEXTS denylist for
  AI-assisted tooling/development/review and AI-generated content/images.
  (ref-034)
- **behavioral-nudge.py syntax error**: muted print left multi-line dict
  literal active, causing SyntaxError. Restored print call. (ref-035)
- **constraint-pinning.py empty main()**: main() was `pass` with no
  `__main__` guard — hook never wrote markers or re-injected constraints.
  Restored full implementation. (ref-036)
- **check-push-green.py empty main()**: main() was `pass` — hook never
  blocked any git push. Restored full implementation with stdin parse,
  PreToolUse/exec/git-push checks, test runner, held-out gap. (ref-037)
- **check-push-green.py gap check investigation**: empty tests/validation/
  makes gap check dead code (val_passed=False never blocks). No code
  change — test infrastructure gap. (ref-038, investigated)
- **.gitignore .pytest_cache**: added .pytest_cache/ to .gitignore
  (was not ignored despite internal .gitignore). (ref-039)
- **audit.py __main__ guard check**: added check [2b] to detect hook
  scripts missing `if __name__ == "__main__"` guard. Would have caught
  iters 4-6 bugs. Updated check count 24->25. (ref-040)
- **check-ai-signature.py multi-context strip**: check_text with two
  allowed contexts returned True (blocked) because loop stripped one
  context at a time. Fixed: strip ALL contexts cumulatively, then check.
  (ref-041)
- **destructive-gate.py SQL false positives**: SQL_DESTRUCTIVE regex
  matched echo/grep/cat commands containing keywords. Added SQL_CLIENTS
  regex — gate now requires both SQL_DESTRUCTIVE and SQL_CLIENTS. (ref-042)
- **destructive-gate.py WinRM false negatives**: Remove-Item with path
  before flags, or no target, was not blocked. Added WIN_RM_RE_PATH_FIRST
  and WIN_RM_RE_NOTARGET patterns. (ref-043)
- **validate-skill-format.py AI signature false positives**: flagged
  descriptive contexts inconsistently with check-ai-signature.py. Added
  AI_ALLOWED_CONTEXTS tuple matching check-ai-signature.py. (ref-044)
- **destructive-gate.py force-with-lease**: GIT_FORCE_PUSH blocked
  `--force-with-lease` (safe alternative). Removed from alternation,
  added negative lookahead. (ref-045)
- **check-ai-signature.py .bak file filtering**: substring match
  filtered .bak variants as self-files. Replaced with regex matching
  exact filename at end of git diff path. (ref-046)
- **silent-error-review.py warning+error lines**: signal_lines stripped
  entire lines containing warning keywords, causing false negatives when
  a line had both warning AND error indicators. Fixed: only strip if
  noise without error. (ref-047)

### Fixed (iter 8.4 — continuous improvement directive: data integrity + gap check activation)

- **refinements.log.jsonl duplicate IDs**: 48 entries had 30 unique IDs
  (16 duplicates) — rollback-by-ID was ambiguous. Renumbered all entries
  sequentially ref-001 to ref-048. (ref-048, LOOP 1)
- **audit.py refinement ID uniqueness check**: added check [25] to
  detect duplicate IDs in refinements.log.jsonl. Prevents recurrence.
  Check count 25->26. (ref-048, LOOP 2)
- **tests/validation/ populated**: 4 infrastructure smoke tests added
  (audit passes, skill-format passes, refinement-evidence valid).
  Activates check-push-green.py gap check (was dead code with empty
  validation/). Rule 16 reward hacking guard now operational. (ref-048,
  LOOP 3)
- **manifest.json stale purposes**: diagnosing-bugs and primeagent-
  reference had outdated purpose fields vs SKILL.md descriptions. Synced
  to current frontmatter. (ref-048, LOOP 4)
- **audit.py manifest/SKILL.md sync check**: added check [26] to detect
  stale manifest purposes vs SKILL.md descriptions. Prevents recurrence.
  Check count 26->27. (ref-048, LOOP 4)

### Fixed (iter 8.2 — self-improvement loop: stale refs + model info + encoding)

- **dispatching-parallel-agents model info**: skill table said
  implementer/debugger use "parent" model, but `agents/implementer.md`
  and `agents/debugger.md` pin `model: swe-1-7`. Updated table and
  Model Selection section to reflect SWE-1.7 (free, 262K) as default
  for implementers. Source: cognition.com/blog/swe-1-7.
- **subagent-router stale model info**: 5 agent profiles had stale
  SWE-1.6/$ cost info. Updated all to SWE-1.7 (262K, FREE), added
  `subagent_explore` PAID warning, fixed 4 references to pruned
  `subagent-driven-development` skill.
- **Agent profiles AgentCARD**: added bottleneck role awareness to
  all 5 profiles (architect=planner for debugging, reviewer=reviewer
  for doc analysis, researcher=executor for research). Source:
  arXiv:2606.20629.
- **MODEL-GUIDE.md benchmarks**: added SWE-1.7 vs GLM-5.2 comparison
  table (FrontierCode 42.3% vs 24.5%, Terminal-Bench 81.5% vs 81.0%,
  SWE-Bench 77.8% vs 74.5%) and 10-task routing matrix. Source:
  cognition.com/blog/swe-1-7.
- **render-graphs.js stale ref**: example used `subagent-driven-
  development` (deleted in iter 8.0). Replaced with `obsidian-
  workflow` (only skill with Mermaid diagrams).
- **obsidian-workflow validators rename**: 3 scripts had stale
  `obsidian-project-docs` in docstrings/argparse (skill renamed to
  obsidian-workflow in iter 8.0). Fixed to "Obsidian codebase wiki".
- **primeagent-reference adaptation status**: SKILL.md said "9/9
  features adapted" but 2 were pruned (session-checkpoint, heartbeat).
  Fixed to "7/9 adapted, 2 pruned" — consistent with README bullets.
- **README adaptation status**: 2 stale "9/9 features" references
  (lines 262, 288) contradicted own bullet list ("2 pruned") and
  primeagent-reference skill. Fixed to "7/9 adapted (2 pruned)".
- **install.ps1/export.ps1 encoding**: PowerShell 5.x read UTF-8
  files without BOM as Windows-1252, causing parser errors on
  em-dashes. Added UTF-8 BOM (EF BB BF) to both .ps1 files.
- **CHANGELOG missing iter 8.2**: Unreleased section had iter 8.1
  and 8.0 but was missing 9 refinements (ref-011 to ref-019) from
  subsequent sessions. Added iter 8.2 Fixed section.
- **TOOLS-MAP missing hook entry**: hooks table missing
  `behavioral-nudge.py` (UserPromptSubmit) — added in commit bfef22b
  but not documented. Added row.
- **README hooks table missing 2 entries**: missing `validate-
  mermaid.py` (PreToolUse write/edit) and `behavioral-nudge.py`
  (UserPromptSubmit). Added 2 rows to match hooks.v1.json.
- **SKILL-TIERS stale token counts**: 3 skills updated after
  2026-08-20 measurement had stale counts: primeagent-reference
  7876→10091 (28% off), obsidian-workflow 14798→17435 (18% off),
  dispatching-parallel-agents 9710→10065 (3.7% off). Updated counts
  + measurement date to 2026-08-22.
- **manifest.json vague purpose fields**: planning-pipeline and
  obsidian-workflow both had the identical string "merged planning/
  obsidian pipeline" as their purpose — two different skills with the
  same description. Fixed to their real SKILL.md frontmatter
  descriptions (spec/tickets/questionnaire; Obsidian 4 modes).
- **SKILL-TIERS 4 more stale token counts**: writing-plans 1746→1704,
  executing-plans 551→535, wayfinder 2936→2938, playbook 2400→1496
  (60% off — playbook SKILL.md was rewritten shorter in iter 8.1).
  Updated 4 counts in the planning/decision domain rows.
- **Planning flow unification (grilling vs ask-matt)**: grilling
  SKILL.md mandated writing-plans as its ONLY terminal state ("Do NOT
  invoke any other implementation skill"), but ask-matt SKILL.md
  routed grilling → planning-pipeline (Spec) → planning-pipeline
  (Tickets) → implement without mentioning writing-plans. Unified:
  grilling now offers both exits (planning-pipeline/Tickets canonical,
  writing-plans alternative for single-session detailed plans);
  ask-matt now mentions writing-plans → executing-plans as alternative
  to Tickets → implement; writing-plans now documents its input
  sources and positions itself vs Tickets mode. Updated 3 token
  counts (grilling 2511→2656, writing-plans 1704→1785, ask-matt
  2893→3037). Synced 3 skills to live.

### Fixed (iter 8.0 — doc count consistency + hook events accuracy + legacy cleanup)

- **Deleted 3 legacy skill dirs**: obsidian-project-docs (consolidado em
  obsidian-workflow), subagent-driven-development (consolidado em
  dispatching-parallel-agents), systematic-debugging (consolidado em
  diagnosing-bugs). Reduzido 49→46 skills. README "Merged from" table
  mantida como histórico de consolidação.
- **TOOLS-MAP.md stale counts**: "46 skills" → "49 skills" → "46 skills"
  (legacy cleanup), "11 scripts" → "12 scripts", "6 eventos" → "8 eventos",
  "25 ativas + 2 modo-dependentes" → "26 ativas + 2 modo-dependentes"
  (28 total), "19/27" → "19/28", "8 excluídas" → "9 excluídas".
  Verified against disk and docs.devin.ai/cli/extensibility/hooks/overview
  (8 events). Bundle uses 6 of 8; PermissionRequest and SessionEnd
  documented as available but unused.
- **README.md stale counts**: diagram "46 skills" → "49 skills" →
  "46 skills", "6 events" → "8 events"; hooks header "6 events" →
  "8 events"; install summary "6 hook events" → "8 hook events";
  badge skills-49 → skills-46.
- **SKILL-TIERS.md**: typo double period `PAGO)..` → `PAGO).`.
- **manifest.json**: removed 3 legacy skill entries, skill_count 49→46,
  tool_count 27→28.
- **audit.py check [24]**: new check verifies TOOLS-MAP.md and README.md
  counts match disk reality (skills, scripts, hook events, tools, excluded).
  Prevents future stale-count regressions.
- **validate-refinement-evidence.py**: added PowerShell cmdlet patterns
  (Select-String, Get-ChildItem, etc.) to REPRODUCIBLE_PATTERNS — fixes
  false phantom-guardrail flag on Windows-documented refinements.
- **Sources**: docs.devin.ai/cli/extensibility/hooks/overview (8 events),
  docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks (event details),
  Get-ChildItem skills/scripts (disk counts).

### Changed (iter 7.3 — política de modelos CONDICIONAL)

- **Política alterada de FREE-ONLY para CONDICIONAL**: modelos pagos agora
  são permitidos para subagents **quando o parent está em modelo pago**
  (usuário fez `/model opus`, `/model sonnet`, etc.). Quando o parent está
  em modelo FREE (default `glm-5-2`), subagents DEVEM ser FREE.
- **Caso 1 (Parent FREE)**: FREE-ONLY mantido. `subagent_explore` (SWE-1.6
  pago), `swe` alias (SWE-1.7 Lightning pago) e todos os modelos pagos
  proibidos para subagents.
- **Caso 2 (Parent PAGO)**: `subagent_explore` (SWE-1.6, $0.5/$2.5) é
  permitido — mais barato que o parent. `subagent_general` herda o modelo
  pago do parent. Custom profiles com `model: swe-1-7` continuam FREE
  (preferir quando possível).
- **Arquivos atualizados**: `AGENTS.md` Rule 20, `MODEL-GUIDE.md` (novo
  protocolo condicional com 2 casos), `TOOLS-MAP.md`, e 5 skills
  (`dispatching-parallel-agents`, `primeagent-reference`, `context-folding`,
  `obsidian-workflow`, `self-extend`) — todas as annotations "NUNCA usar
  `subagent_explore`" agora dizem "NUNCA usar quando parent é FREE".

### Fixed (iter 7.1 — `subagent_explore` PAGO bug)

- **BUG CRÍTICO DE CUSTO (iter 7.1)**: o profile built-in `subagent_explore`
  roda no **default subagent model (SWE-1.6, PAGO $0.5/$2.5 MTok)**. Não há
  override local — apenas enterprise settings podem mudar isso. O system
  prompt do Devin CLI recomenda `subagent_explore` para read-only exploration,
  então qualquer dispatch desse profile incorre em custo.
- **Solução**: adicionada regra em `AGENTS.md` (Rule 20) e `MODEL-GUIDE.md`
  proibindo `subagent_explore`. Direcionado para o profile customizado
  `researcher` (`agents/researcher.md`, pin `model: swe-1-7`, gratuito, 262K)
  que tem as mesmas capacidades read-only.
- **Skills corrigidas**: 5 skills (`dispatching-parallel-agents`,
  `primeagent-reference`, `context-folding`, `obsidian-workflow`,
  `self-extend`) tinham 10 referências ativas a `subagent_explore` como
  recomendação de uso. Todas substituídas por `researcher` com annotation
  "NOT `subagent_explore` — PAID SWE-1.6".
- **Fonte**: docs.devin.ai/cli/subagents — "subagent_explore: The default
  subagent model — a fast, cheap model (SWE-1.6 by default)".

### Changed (iter 7.0 — FREE-ONLY policy enforcement)

- **Protocolo de escalada pago REMOVIDO**: `MODEL-GUIDE.md` tinha um
  protocolo de 6 níveis que recomendava GLM-5.2 Max ($0.7/$2.2),
  DeepSeek V4 Flash ($0.14/$0.28), Opus ($5/$25) e GPT-5.4 ($2.5/$15)
  como fallbacks. Substituído por protocolo FREE-ONLY: se GLM-5.2 High +
  SWE-1.7 fan-out falharem, parar e reportar ao usuário — nunca escalar
  para pago.
- **AGENTS.md Rule 20**: "Só usar como fallback após 3+ tentativas
  documentadas" → "🚫 NUNCA usar modelos pagos. Se falharem, parar e
  reportar ao usuário."
- **Skills corrigidas**: `dispatching-parallel-agents`, `primeagent-reference`
  e `self-extend` recomendavam `sonnet` (pago, $2/$10) e `SWE-1.6` (pago,
  $0.5/$2.5) para subagent profiles. Corrigido para `SWE-1.7` (gratuito,
  262K) em todas as referências.
- **TOOLS-MAP.md**: tabela de aliases agora marca todos os modelos pagos
  com "**PAGO** — não usar" e adiciona `swe-1-7-medium` (gratuito) como
  alternativa.
- **Regra ABSOLUTA adicionada**: "NUNCA usar modelos pagos. Os modelos
  gratuitos (GLM-5.2 High + SWE-1.7) cobrem 100% dos casos."

## [2.5.1] - 2026-08-21

GLM-5.2 High + SWE-1.7 optimization. 9 iterations, all changes verified against
primary sources (`devin models list`, docs.devin.ai, cognition.com, z.ai).

### Fixed (CRÍTICO — agents/ usando modelo PAGO em vez de gratuito)

- **BUG CRÍTICO DE CUSTO**: todos os 5 agents/ (architect, debugger,
  implementer, researcher, reviewer) usavam `model: swe` que é alias para
  `swe-1.7-lightning` (PAGO, $2.5/$12.5 MTok, 202K context). O modelo
  gratuito é `swe-1-7` (SWE-1.7 Max, 262K context, Free). Corrigido: todos
  os agents/ agora usam `model: swe-1-7`. Descoberto via `devin models list`.
- **Impacto**: cada subagent dispatch estava custando ~$2.5/$12.5 MTok
  desnecessariamente. O modelo gratuito tem MAIS contexto (262K vs 202K).
  Correção salva dinheiro E dá mais headroom de contexto.
- **SWE-1.7 context window** — corrigido de "200K/256K ambíguo" para
  definitivamente 262K. Verificado contra `devin models list` e fontes
  primárias (cognition.com/blog/swe-1-7, HuggingFace Kimi-K2.7-Code card).
- **BOM em agent files**: 4 de 5 agent files tinham BOM (EF BB BF) no início.
  BOM em YAML frontmatter pode impedir o parser de reconhecer `---`, fazendo
  `model: swe-1-7` ser ignorado — agent cairia para SWE-1.6 (PAGO). BOM
  removido. `install.ps1`/`install.sh` agora stripam BOM automaticamente.
- **`validate-mermaid.py` fail-closed → fail-open**: quando Node.js/mermaid
  indisponível, o hook bloqueava TODOS writes com mermaid. Corrigido para
  fail-open (consistente com os demais hooks do bundle).
- **`constraint-pinning.py` marker not session-scoped**: marker usava filename
  fixo sem session_id — sessions paralelas sobrescreviam markers um do outro.
  Corrigido: filename inclui session_id. SessionStart limpa markers stale.
- **`constraint-pinning.py` dead code removido**: `inject("PostCompaction")`
  era chamado mas PostCompaction não suporta `additionalContext` (per docs).
  Chamada removida; mecanismo correto é marker-based re-injection no
  UserPromptSubmit.
- **`refine-review-prompt.py` skill ref fixa**: referência a skill `refine`
  inexistente → `primeagent-reference` Refine mode.
- **`mermaid-parse-check.js` hardcoded paths**: paths machine-specific
  (`C:\Users\Fingertech\scoop\...`) → portable lookup (require.resolve,
  npm root -g, Linux paths, Windows fallback).
- **MODEL-GUIDE.md dados de GLM-4.6 atribuídos a GLM-5.2**: max output
  128K → 131,072. Custos $1.4/$4.4 removidos (GLM-5.2 High é gratuito).
- **24 broken skill references**: `subagent-driven-development`→`dispatching-parallel-agents`,
  `systematic-debugging`→`diagnosing-bugs`, `to-spec`→`planning-pipeline`,
  `find-skills`→`tool-and-skill-discovery`, `grill-with-docs`→`grilling`,
  `wiki-audit/audit.py`→`obsidian-workflow/scripts/audit.py` (11 skills).
- **`hooks.v1.json` `%APPDATA%` → `{{APPDATA}}`**: sintaxe Devin-native.
- **`audit.py` live_base stale**: `C:\Users\leand\...` → auto-detect
  (WSL/Linux/Windows).

### Added

- **Rule 20: Model-aware operation** — GLM-5.2 High (200K, gratuito, thinking,
  tool-use nativo) é primário; SWE-1.7 (262K, gratuito, self-compaction,
  1000 TPS) é subagent via `model: swe-1-7`. Non-pinned. Ver MODEL-GUIDE.md.
- **MODEL-GUIDE.md** — specs verificadas (GLM-5.2 + SWE-1.7), linhagem,
  estratégia de model pin, context budget, protocolo de escalada (6 níveis),
  reasoning effort guide, subagent vs compaction decision table.
- **TOOLS-MAP.md** — mapeamento completo do runtime: 27 ferramentas, 7
  subagentes, 6 eventos de hook, 11 scripts, configs, modos, modelos.
- **validate-tool-args.py**: 6 validators adicionados (`ask_user_question`,
  `browser_preview`, `close_browser_preview`, `todo_write`, `apply_patch`,
  `exit_plan_mode`). Matcher depois otimizado 28→19 tools (removidos 9 no-ops).
- **install.ps1/install.sh**: `strip_bom` (remove BOM de agent files) e
  `dedup_agents_md` (remove duplicatas lowercase em FS case-sensitive).
- **context-budget.py**: reporta share de 200K (GLM-5.2) e 262K (SWE-1.7).
- **SKILL-TIERS.md**: custos de tokens medidos (bytes÷4), modelos alvo,
  anti-patterns expandidos.

### Changed

- **`silent-error-review.py` scope narrowed (noise reduction)** — PostToolUse
  matcher de `""` (all tools) → `^(exec|mcp_call_tool)$`. ALTK scope
  (arXiv:2603.15473): "best suited for verbose/tabular responses". Regexes
  tightened (error requer colon, test-failures requer count > 0). Max 1
  finding por call. Addresses PR #1 review comment on hook noise.
- **`validate-tool-args.py` matcher narrowed (latency reduction)** — 28→19
  tools. Removidos 9 tools com checks triviais/no-ops. Zero perda de
  validação real. Saves ~9 Python process spawns per session.
- **SKILL-TIERS.md reescrito** — custos medidos em vez de estimativas.
- **README.md** — 8 inconsistências corrigidas (rules 18→19, skills 47→46,
  tools 15→28→19, events 4→6, scripts 4→11).

### Verified

- `devin models list` — primary source (swe-1-7 = Free/262K, swe alias = Lightning/$2.5/202K)
- docs.devin.ai/cli/subagents — default router = SWE-1.6
- docs.devin.ai/cli/models — short names resolve to latest
- cognition.com/blog/swe-1-7 — SWE-1.7 specs (Kimi K2.7 base, self-compaction, 1000 TPS)
- HuggingFace Kimi-K2.7-Code card — Context Length: 256K (262,144 tokens)
- z.ai/blog/glm-5.2 — GLM-5.2 specs (gratuito, 200K, 131K max output)

## [2.4.0] - 2026-08-18

### Added

- **Rule 19: Never read secrets or sensitive env vars** — new pinned
  governance rule. Never `read`, `cat`, `echo`, `print`, or output API keys,
  tokens, passwords, private keys, or `.env` secret values. Use them (pass to
  commands, reference by variable name) but never display their contents. If
  a key/env var is missing, empty, or doesn't behave as expected, say so
  without exposing the value. Pinned into `constraint-pinning.py` (survives
  compaction). Pinned set is now Rules 2, 5, 7, 12-19.
- **`context-window-hygiene` skill** — clear vs compact, MCP paranoia,
  lost-in-the-middle (arXiv:2307.03172).
- **`mcp-context-audit` skill + `mcp-context-audit.py` script** — estimates
  per-server tool-definition token cost; flags >15 tools/server and >5%
  window share.
- **`context-budget.py` script** — SessionStart hook that reports AGENTS.md
  token cost to stderr. Transparency without context bloat.
- **`SKILL-TIERS.md`** — skills categorized by domain with token costs
  (~1700 tok vs ~2094 for `skill list`).

### Pruned (orphaned/duplicated — no consumers)

- **`graphify` skill** — 9659 tok (a mais cara), sem `graphify-out/` em
  nenhum projeto ativo. CLI `graphify.exe` instalado mas sem uso pelo agente.
  Rule 6 (graphify trigger) removida do AGENTS.md. 47 → 46 skills.
- **`post-compaction-reminder.py`** — órfão (0 hooks), duplicado por
  `constraint-pinning.py` (superior: dinâmico, 9 regras pinned, em 3 hooks).
- **MCP `arxiv`** — 0 consumidores (grep por `mcp__arxiv` em skills/ vazio).
  `observability-quality` cita `arxiv.org/abs/...` (URL de paper), não o MCP.
- **`heartbeat` skill** — emulação PrimeAgent que não fita Devin CLI
  (single-process, sem daemon). OS scheduler + script launches nova sessão
  não funciona no runtime atual.
- **`session-checkpoint` skill** — mesma razão. Emulação daemon-backed
  reattach não funciona em single-process.

### Consolidated (overlaps merged with mode selectors — content preserved)

- **`grilling`** ← `grill-me` + `grill-with-docs` (wrappers de 5-6 linhas
  que só redirecionavam). Modos: Default, Stateless, With-docs.
- **`diagnosing-bugs`** ← `systematic-debugging`. Pipeline unificado de
  6 fases. Arquivos de suporte (`root-cause-tracing.md`,
  `defense-in-depth.md`, `condition-based-waiting.md`) movidos para
  `diagnosing-bugs/`.
- **`tool-and-skill-discovery`** ← `find-skills`. Discovery + install/evaluate
  em uma skill.
- **`dispatching-parallel-agents`** ← `subagent-driven-development`. Dispatch
  geral + modo plan execution. Scripts e prompts de suporte movidos.
- **`planning-pipeline`** ← `to-spec` + `to-tickets` + `to-questionnaire`.
  Modos: Spec, Tickets, Questionnaire.
- **`obsidian-workflow`** ← `obsidian-project-docs` + `vault-organizer` +
  `wiki-audit` + `memory-bridge`. Modos: Build, Reorganize, Audit,
  Cross-session. Templates, references e scripts movidos.
- **`primeagent-reference`** ← `a2a-mailbox` + `refine` + `subagent-router`.
  Modos: Reference Card, A2A Messaging, Refine, Subagent Router.

### Fixed

- **`hooks.v1.json` leftover no global** — arquivo user-level com paths
  `%APPDATA%` literais não expandidos causava `validate-mermaid.py` e outros
  hooks a falhar com `[Errno 2] No such file or directory`. O Devin CLI lia
  o arquivo (não deveria — user-level hooks vão em `config.json` desde
  v2.2.1). Arquivo deletado do global.
- **`audit.py` rule detector false positive** — `6. **` era detectado como
  substring de `16. **`, inflando a contagem de regras. Ancorado com `\n`
  prefix para matching start-of-line.

### Changed

- **62 → 46 skills** (-16, 26% redução). Mesma cobertura funcional, menos
  namespace bloat, menos manutenção.
- **17 → 18 rules** (Rule 6 removida, Rule 19 adicionada). Regras pinned:
  2, 5, 7, 12-19.
- **12 → 11 scripts** (remoção de `post-compaction-reminder.py`).
- **2 → 1 MCP** (remoção de `arxiv`).
- **AGENTS.md enxugado**: 25KB → 18.5KB (~6263 → ~4614 tok). Non-pinned rules
  comprimidas para one-liners referenciando skills.
- **`constraint-pinning.py`** — Rule 19 adicionada ao `PINNED_CONSTRAINTS`
  e `key_phrases`.
- **`agents/researcher.md`** — removida referência a `graphify` (query mode).
- **`obsidian-workflow/SKILL.md`** — 9 referências a `graphify` substituídas
  por `ls`/`tree`/`git ls-files`.
- **Version 2.3.0 → 2.4.0** (manifest). README badges, counts, skill tables
  atualizados. SKILL-TIERS.md reescrito com 46 skills.
- **`audit.py`** — contagens e listas de sync atualizadas para 46 skills,
  11 scripts, 18 rules, v2.4.0.

## [2.3.0] - 2026-08-18

### Added (context window management — from "Context Windows Explained for Coding Agents", Matt Pocock)

- **Rule 18: Keep the context window lean** — new pinned governance rule.
  Context window = input + output tokens (hard-capped); lost-in-the-middle
  deprioritizes the middle of long chats; default to `clear` over `compact`;
  keep rules files small; audit MCP servers before adding; bigger window ≠
  better retrieval. Pinned into `constraint-pinning.py` (survives compaction).
- **`context-window-hygiene` skill** — practical user-facing hygiene: clear vs
  compact, lean rules, MCP paranoia, subagent context savings, model selection
  heuristic. Backed by lost-in-the-middle (arXiv:2307.03172).
- **`mcp-context-audit` skill + `mcp-context-audit.py` script** — estimates
  per-server tool-definition token cost; flags >15 tools/server (selection
  accuracy degrades, arXiv:2606.30317) and >5% window share. `--config` static
  mode + `--tools` measured mode (fed from `mcp_list_tools`).
- **`context-budget.py` script** — SessionStart hook that reports the AGENTS.md
  token cost to stderr. Transparency analogous to Claude Code's `/context`,
  without adding context bloat (stderr only). Warns at ≥10% of a 200k window.

### Changed

- **AGENTS.md enxugado: 25KB → 18KB (~6263 → ~4546 tokens).** Non-pinned rules
  compressed to terse one-liners referencing skills; pinned rules (2, 5, 7,
  12-18) keep full detail. Reduces lost-in-the-middle tax on every session.
- **`constraint-pinning.py`** — Rule 18 added to `PINNED_CONSTRAINTS` and
  `key_phrases`; pinned set is now Rules 2, 5, 7, 12-18.
- **`config.json` / `hooks.v1.json`** — `context-budget.py` added to
  SessionStart alongside `constraint-pinning.py`.
- **Version 2.2.5 → 2.3.0** (manifest). README badges, counts, rules table,
  hooks table, and skill listing updated (62 skills, 18 rules, 12 scripts).
- **`audit.py`** — hardcoded expectations updated to the true counts
  (62 skills, 18 rules, 12 scripts, version 2.3.0); new skills added to the
  live-vs-bundle sync list.
- **`SKILL-TIERS.md`** — novo arquivo de discovery rápido. Skills
  categorizadas por domínio de uso (núcleo, docs, programação, debug, git,
  jira, obsidian, planejamento, pesquisa, meta, setup, artefatos de pesquisa,
  outros) com custo em tokens e quando invocar. ~1500 tok vs ~2094 tok de
  `skill list`. Referenciado em AGENTS.md Rule 4 e README.

## [2.2.3] - 2026-08-15

### Fixed (coverage gaps vs official tool list)

- **validate-tool-args.py missing 7 tools** — the official docs list
  `get_output`, `write_to_process`, `kill_shell`, `skill`, `request_scope`,
  `mcp_list_tools`, `mcp_list_servers` as available tool names. The validator
  had no checks for them, so calls with missing required args (e.g. `get_output`
  without `shell_id`) passed silently. Added validators for all 7.
- **validate-tool-args.py early-exit on empty tool_input** — `if not tool_input`
  treated `{}` as falsy and exited before validating. Tools like `get_output`
  and `kill_shell` that require args but received `{}` were allowed. Fixed:
  only skip on non-dict input, not empty dict.
- **researcher.md model: swe** — `swe` is not a documented model value.
  Changed to `sonnet` (documented in the subagent profiles example).
- **researcher.md BOM** — UTF-8 BOM (EF BB BF) removed.
- **Matcher expanded** — config.json and hooks.v1.json matchers now include
  the 7 newly-validated tool names.

## [2.2.2] - 2026-08-15

### Fixed (critical — hook commands used %APPDATA% which is not expanded)

- **`%APPDATA%` is not expanded in hook commands** — the hook shell does not run
  through cmd.exe, so `%APPDATA%` stays literal and the path becomes
  `D:\...\%APPDATA%\devin\scripts\...` (No such file or directory). All hooks failed
  to find their scripts. Live config.json now uses absolute paths
  (`C:/Users/leand/AppData/Roaming/devin/scripts/...`).
- **Bundle uses `{{APPDATA}}` placeholder** — portable across users/machines.
  `install.ps1` expands `{{APPDATA}}` to `$env:APPDATA` (forward slashes) during
  merge. `export.ps1` normalizes absolute APPDATA paths back to `{{APPDATA}}`.
- **audit.py** — regex now matches `scripts/` and `scripts\`; warns on `%APPDATA%`;
  normalizes `{{APPDATA}}` vs absolute path before comparing live vs bundle hooks.

## [2.2.1] - 2026-08-15

### Fixed (critical — hooks at wrong location)

- **hooks.v1.json is not a valid user-level location** — the docs
  ([Where Hooks Live](https://docs.devin.ai/cli/extensibility/hooks/overview#where-hooks-live))
  list `hooks.v1.json` only under project-level (`.devin/hooks.v1.json`). At user-level,
  hooks must be in `config.json` under the `"hooks"` key. The standalone `hooks.v1.json`
  at `%APPDATA%\devin\` was silently ignored. Hooks are now merged into `config.json`.
- **mcp_config.json BOM** — file had UTF-8 BOM (EF BB BF), removed.
- **mcp_config.json undocumented fields** — `arxiv` server had `transport: stdio` (not
  documented for stdio servers; transport is inferred from `command`) and a `note` field
  (not in the schema). Both removed.
- **refine-review-prompt.py exit code** — printed `{"decision":"block"}` but exited with
  0 instead of 2. Changed to exit 2 for consistency with all other blocking scripts.
- **export.ps1 / install.ps1 / audit.py** — updated to read/write hooks from `config.json`
  instead of standalone `hooks.v1.json`. The bundle keeps `hooks.v1.json` for project-level
  use (`.devin/hooks.v1.json`).

## [2.2.0] - 2026-08-15

### Fixed (critical — hooks were non-functional)

Verified every hook script against the official Devin CLI hook contract
([Lifecycle Hooks](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks),
[Overview](https://docs.devin.ai/cli/extensibility/hooks/overview)). Nine defects
made the hooks silently no-op:

- **`tool` → `tool_name`** — every script read `data["tool"]`, which does not exist in the payload. All tool checks always saw an empty string and never fired. Affected all 9 scripts.
- **Exit code 1 → 2** — blocking requires exit code **2**; exit 1 is "error, logged but doesn't block". Every block was being ignored. Affected 7 scripts.
- **`tool_response` schema** — real shape is `{success, output, error}`, not `{exit_code, stderr, results, content, matches}`. `silent-error-review.py` never detected anything.
- **`Stop` payload** — has `stop_hook_active`, not `event`. `check-ai-signature.py` and `refine-review-prompt.py` exited early on every Stop event.
- **`PostCompaction` cannot inject context** — only `UserPromptSubmit`, `SessionStart`, and `PostToolUse` support `hookSpecificOutput.additionalContext`. Constraint Pinning was rewritten as a three-event flow: detect at PostCompaction → marker → re-inject at UserPromptSubmit.
- **Unanchored matchers** — `"read"` also matched `notebook_read`, `read_subagent`, and `mcp_read_resource`; `"write"` also matched `write_to_process`. Matchers are now anchored regexes (`^exec$`, `^(write|edit)$`, explicit tool list).
- **Missing `decision`/`reason` output** — blocks now return `{"decision":"block","reason":...}` so the agent receives an actionable explanation instead of a bare non-zero exit.
- **`hook_event_name` dispatch** — multi-event scripts now dispatch on `hook_event_name` instead of guessing from absent fields.
- **Stop-hook loop risk** — `refine-review-prompt.py` now honours `stop_hook_active` and consumes its marker before blocking, so it can block at most once.

Also fixed: `DEVIN_PROJECT_DIR` is now used for the project root; `rm -rf` target
parsing rewritten (whitelist by path prefix, handles multiple targets and shell
operators); `validate-skill-format.py` no longer false-positives on the prose word
"task (" and now joins folded multi-line YAML frontmatter values.

### Removed

- **`post-compaction-reminder.py`** — printed a reminder to stdout on `PostCompaction`, an event that cannot inject context, so it never reached the agent. Superseded by `constraint-pinning.py`.

### Added
- **Rule 14:** Constraint Pinning survives compaction — governance constraints re-injected after compaction with hash verification (arXiv:2606.22528v2)
- **Rule 15:** Refinement evidence must be reproducible — phantom guardrails occur in 25% of self-improvement runs (arXiv:2607.13083)
- **Rule 16:** Self-improvement loops produce 47-74% illusory gains — validate with held-out tests (ICLR 2026 Workshop)
- **5 new scripts:**
  - `destructive-gate.py` — PreToolUse hook blocking `rm -rf /`, `git push --force` without `--dry-run`, `DROP TABLE`, `chmod -R 777 /` (arXiv:2607.07405, KDD 2026 Workshop)
  - `silent-error-review.py` — PostToolUse hook flagging `success:true` responses that carry error indicators, empty reads, or no-match searches (ALTK, ACM CAIS 2026)
  - `constraint-pinning.py` — three-event Constraint Pinning across PostCompaction / UserPromptSubmit / SessionStart (arXiv:2606.22528v2)
  - `validate-tool-args.py` — PreToolUse hook validating paths, regexes, URLs, and subagent profiles for 15 tools (ALTK SPARC, ACM CAIS 2026)
  - `validate-refinement-evidence.py` — manual-run script checking `refinements.log.jsonl` for phantom guardrails
  - `validate-skill-format.py` — manual-run script scoring SKILL.md against the 8-point quality checklist
- **arxiv MCP server** — Domain-Specific Adapter pattern, 14 tools, for Rule 12 enforcement (arXiv:2606.30317 evaluation)
- **3 new hook events wired** — `PostToolUse` (silent error detection), `UserPromptSubmit` and `SessionStart` (Constraint Pinning re-injection and marker cleanup)
- **Held-out gap check** in `check-push-green.py` — blocks push when validation passes but held-out fails
- **MCP evaluation criteria** in Rule 13 — 5 patterns, 4 anti-patterns, tool count < 10-15 (arXiv:2606.30317)
- **Dynamic Subagent Construction (AOrchestra 4-tuple)** documented in `self-extend` skill (ICML 2026, arXiv:2602.03786)
- **Role Bottleneck Awareness (AgentCARD)** in `subagent-router` skill (arXiv:2606.20629)
- **Phantom Guardrail Check** in `refine` skill Step 1 (arXiv:2607.13083)
- **Elaborate Stagnation Check** in `refine` skill outcome tracking (arXiv:2607.25152)
- **Interaction-Centric Failure Dimension** in `diagnosing-bugs` skill (arXiv:2607.28802)
- **VRR-Stop stopping criterion** in `systematic-debugging` skill (arXiv:2607.17641)

### Changed
- `hooks.v1.json` — 3 to 6 events, 4 to 7 hook scripts, anchored regex matchers
- `AGENTS.md` — expanded from 13 to 16 rules, added MCP evaluation criteria to Rule 13
- `check-push-green.py` — added held-out gap measurement (Rule 16), skips `--dry-run` pushes
- `check-ai-signature.py` — Stop event now scans unstaged changes in addition to staged
- `README.md` — updated counts (16 rules, 6 events, 7 hook scripts, 2 manual-run scripts), added rules 14-16, documented the hook contract
- `audit.py` — expectations updated to 16 rules / 9 scripts / version 2.2.0

## [2.1.0] - 2026-08-15

### Added
- **Rule 13:** Devin CLI is not a security sandbox — guardrails for untrusted code, MCP servers, skills, and reward hacking
- **7 new skills** from verified PrimeAgent/RLM research:
  - `context-folding` — RLM-style context folding (arXiv:2512.24601), depth=1 only
  - `refine` — Continual Harness self-improvement (arXiv:2605.09998) with auto-trigger, outcome tracking, reward hacking guard
  - `autonomous-gates` — bounded autonomous mode with quality gates
  - `a2a-mailbox` — file-based A2A messaging emulating PrimeAgent's `agent_message.send()`
  - `session-checkpoint` — structured checkpoint for cross-session continuation
  - `heartbeat` — OS-scheduled re-entry via Task Scheduler/cron
  - `primeagent-reference` — reference card of 9/9 adapted features with verified sources
- **`refine-review-prompt.py`** Stop hook for auto-refinement prompts
- **LICENSE** (MIT)
- **SECURITY.md** — security policy documenting guardrails and limitations
- **CONTRIBUTING.md** — contribution guide with skill/rule/hook standards
- **CHANGELOG.md** — this file
- **.github/workflows/ci.yml** — CI: validate JSON + Python + skill frontmatter on push/PR
- **.github/ISSUE_TEMPLATE/** — bug report and feature request templates
- **.github/PULL_REQUEST_TEMPLATE.md** — PR template
- **Rule 12 clause:** "Don't trust ANY subagent return without verification" — subagent returns are leads, not answers

### Changed
- `post-compaction-reminder.py` — now re-primes rules 7-10 (verification, Rule 12, Rule 13) in addition to 1-6
- `check-push-green.py` — added .NET detection (`.sln`/`.csproj`) + `dotnet test`
- `manifest.json` — synced with disk (was missing 9 skills)
- `README.md` — major rewrite: badges, quick start, prerequisites, troubleshooting, bilingual sections, updated counts
- `.gitignore` — expanded with common temp files

### Fixed
- `post-compaction-reminder.py` was missing rules 10-13 — after compaction, verification and security rules were not re-primed
- `check-push-green.py` did not detect .NET projects — C#/F#/VB.NET pushes were not blocked by failing tests
- `manifest.json` was missing 9 skills (jira, observability-quality, context-folding, refine, autonomous-gates, primeagent-reference, a2a-mailbox, session-checkpoint, heartbeat)
- `refine` skill was not autonomous — added auto-trigger (Stop hook + `.refine-pending` marker), outcome tracking (`refinements.log.jsonl`), rollback by ID

### PrimeAgent/RLM Adaptation Status
- **9/9 features adapted** (3 direct, 3 emulated, 1 partial, 2 guardrails)
- All claims verified against primary sources (arXiv, GitHub, PrimeAgent blog, ARC Prize leaderboard)
- 2 errors in source video corrected (GPT-V → GPT-5, Opus-V → Opus 5)

## [2.0.0] - 2026-08-13

### Added
- Rule 12: Maximum precision, zero tolerance for partial verification
- Rule 11: Never fail from failures
- Cross-platform installer (Windows + Linux/macOS)
- Auto-discover skills export (not limited to manifest)
- Secrets masking in export (config.json, mcp_config.json, credentials.toml)
- 5 subagent profiles (architect, debugger, implementer, researcher, reviewer)
- Hooks: check-ai-signature, check-push-green, post-compaction-reminder
- 45 skills (unified, adapted, and original)

### Changed
- Rules framed as negative constraints (evidence: arXiv:2604.11088)
- Post-compaction re-priming (evidence: arXiv:2605.10039 — 5.6% compliance decay per step)

## [1.0.0] - 2026-08-11

### Added
- Initial bundle: AGENTS.md (10 rules), skills, config, hooks, scripts
- Windows installer (install.ps1) and exporter (export.ps1)
