# v3.8.0 final report - agentcraft-rts-v2

Milestone: https://github.com/Leostruka/devin-bundle/milestone/ (v3.8.0)
Branch: `milestone/v3.8.0` (not merged to `main`; review first).
Spec: `.devin/scratch/agentcraft-rts-v2/gdd.md`.
Brief used by implementers: `AGENT-BRIEF.md` (same dir).

## Delivered issues (18/18, dependency order)

| # | PR | Delivered |
|---|----|-----------|
| 119 | #137 | GDD spec: full class/skill/script/extension/event mapping for the RTS overlay |
| 120 | #138 | Event-sourced world engine `world.py`: units, buildings, resources, quests; `events.jsonl` replay is byte-identical; 2s tick deltas |
| 121 | #139 | Renderer foundation: canvas tilemap engine, camera, minimap, themes, zero deps, ~0.1ms/frame for 200 units in Node bench |
| 122 | #140 | Authoritative world map: dir territories, fixed plots, fog-of-war (shroud/explored/lit, 3x3 reveal, 180s decay), contested tiles, POIs, persisted `map.json` |
| 123 | #141 | 11 buildings on plots; `GET /buildings/<id>` inspectors serving real ledger/memory/git/MCP/remote data; real spawn intents only |
| 124 | #142 | Minimap + camera: upsert `hint` pings (file/contested/spawn/decision/fail), click-jump, SPACE cycling, lane tint, right-click order intents |
| 125 | #143 | Unit model: kits from real allowed-tools, tiers from TOOLS-MAP, worker peasants from hook events, class barks + heartbeat notes, fades, level badges |
| 126 | #144 | Selection + command card: box select, control groups, Tab subgroup, dbl-click class sweep, command card from real kits, quest-POI attack snap |
| 127 | #145 | Orders queue: numbered waypoints, shift-queue, ghost queued state, barracks rally->lane, idle-worker cycler |
| 128 | #146 | Comms feed: typed flavored lines from real events, @unit steering -> message intents, raven anim on mailbox deposits, event-sourced scrollback |
| 129 | #147 | War council: PermissionRequest->decision files, stacked pending, answer endpoint 200/409/400, fail-closed timeout verified with real `rts-decision.py --wait`, alert tiers |
| 130 | #148 | Quest system: DAG chains to real issue files, assign via intents, ledger-bound HP/loot, marker states, main/side split |
| 131 | #149 | Economy HUD: real income rates, supply split, upkeep tier alerts, per-hero burn/turns, Economy pane |
| 132 | #150 | Tech tree + spellbook: all 83 real skills grouped by school, cast counts from events, hero spellbook from profile file, armory model tiers from `bundle-models.json`, doctrines from `.devin/memory/` |
| 133 | #151 | Alerts: per-tier WebAudio signatures, breach tiles from failed ledgers (persist + clear on seal), severity stack, Notification opt-in, TUI `[ALERT]` lines, mute persistence |
| 134 | #152 | Office/isometric mode: iso projection shared by render+picking, all 11 buildings reskinned, ambient furniture from real positions, decision summons, theme persisted |
| 135 | #153 | Replay + spectator: `--replay` daemon (seek/4x, deterministic), `/sessions` match history, `/score` screen, spectator token -> server-enforced 403 on POSTs |
| 136 | #154 | Polish: motion glide, walk/work/idle anims, ambience + day/night, sprite raster cache, hotkey audit + guide card |
| 155 | #156 | Post-review audit fixes: `_apply_hook` guard, iso wheel zoom, SW bypass regex, Marketplace `mcp_config.json` + tool counts, done barks + minion grouping, FIFO waypoint chain/consume, Office labels/printer-fire/water-cooler, `/sessions` cache + Web UI Match History, `<700px` mobile tab bar |

## Final gate evidence (milestone branch)

- `python audit.py` -> Errors: 0, Warnings: 0 (ALL 32 CHECKS PASSED)
- `python extensions/rtsd/selftest.py` -> ALL PASS (26+ checks incl. `replay(events.jsonl) == live world (41 events)`)
- `python -m pytest` -> 1685 passed, 4 skipped (~185s). One flake seen during the run
  (`test_check_push_green_blocks` 30s timeout under parallel load); passes in
  isolation (0.52s) and in the clean full run.
- CHANGELOG `[Unreleased]` has a per-issue entry for #120-#136.

## Known gaps (honest list)

- Raven animation + econ/upkeep feed lines are client-side diffs; pure-polling
  clients see lines, not the flight art (#128, #131).
- Alert sound may stay silent until first user gesture (browser autoplay
  policy; fails silently by design).
- Spectator mode is token-scoped; a loopback client presenting the spectator
  token is also read-only (that is what makes it testable) (#135).
- Inter-event replay delay capped at 1s/speed for watchability; state remains
  deterministic (#135).
- Iso minimap has no viewport rect (camera rect has no tile-space shape) (#134).
- `turns_left` needs a heartbeat `status.json` with ctx data, else null (#131).
- #136 fps claim is code-path-verified (sprite cache + culling), not a measured
  capture; `?bench` mode remains for manual verification.
- Issues left open per milestone convention (`Refs` in every PR; close at
  final merge to main).
