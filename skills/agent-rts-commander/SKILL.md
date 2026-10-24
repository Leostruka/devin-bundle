---
name: agent-rts-commander
description: Use when the user wants the live 3D RTS/Tycoon dashboard (DevinCraft / DevTycoon Orchestrator), to launch extensions/agent-rts/, or to emit structured telemetry so units, buildings, particles, and the HUD mirror real agent execution in the browser.
argument-hint: Launch the dashboard, or describe what the game should reflect.
triggers: [user]
---

# Agent RTS Commander

Operate `extensions/agent-rts/`: a local 3D RTS/Tycoon view (Three.js PBR,
dual theme: Medieval / Office Tycoon) over the shared `.devin/rts/` world
state plus live repo telemetry (git, gh issues, ledgers, prompt compiler).

## Launch

```bash
python extensions/agent-rts/bootstrap.py   # once: creates extension .venv
python extensions/agent-rts/server.py      # serves + opens browser
```

- URL: `http://127.0.0.1:8798` (override with `AGENT_RTS_PORT`).
- Deep link a theme: `http://127.0.0.1:8798/#theme=office` or `#theme=medieval`.
- Shares state root `.devin/rts/` with `extensions/rtsd/` (port 8797);
  both can run side by side.
- Self-check: `python extensions/agent-rts/selftest.py`.

## What the game shows

| HUD / visual              | Real source |
|---------------------------|-------------|
| Units (heroes/workers)    | `World.units` + session lanes from hook events |
| Buildings                 | `World.buildings` (town-hall, runeforge, watchtower, portal, ...) |
| Ticket rail (right)       | `gh issue list` via `collectors.py` |
| Topbar gold / ctx / gas   | tokens+cost / context window free % / supply (CPU-RAM) |
| Feed + quest log          | `World.feed`, `.devin/rts/` quests |
| Decisions modal           | `.devin/rts/decisions/d*.json` pending files |

## Emitting telemetry

Events are plain JSON envelopes appended to `.devin/rts/events.jsonl` and
applied to the event-sourced `World`. Three paths, pick one:

1. **Direct POST** (daemon up):
   `POST http://127.0.0.1:8798/event` with
   `{"type": "hook.posttooluse", "tool": "edit", "session_id": "...",
     "payload": {...}, "ts": <epoch>}`.
2. **Hook tap**: `python scripts/rts-emit.py` with the Devin hook payload on
   stdin. Set `RTSD_PORT=8798` to hit agent-rts; if the daemon is down it
   appends straight to `events.jsonl` (shared root, still works).
3. **Intent files**: write `.devin/rts/intents/i<ms>.json`
   (`{"kind": "order"|"spawn"|"goal"|"message"|"answer", ...}`) or use
   `scripts/rts-intents.py`. Orders are surfaced to the orchestrator; the
   game never auto-executes them.

Event-to-visual mapping (server `fx_for_event`):

| Event | In-game effect |
|-------|----------------|
| `hook.posttooluse` (write/edit/exec) | green code bubble at the unit/building |
| `hook.posttooluse` (skill/todo/ask)  | blue design bubble |
| `hook.posttooluse` (read/search/web/mcp) | purple research bubble |
| `hook.posttooluse` with `tool_response.success == false` | red bug bubble; `tests_red` alert if the command looks like pytest/lint/audit |
| `decision.created` | `gate_flash` at the watchtower + decisions modal |
| `intent.created` with `order: god_power` | meteor strike at `x,y` |

Building routing uses `world.TOOL_TO_BUILDING` when no unit lane matches.

## Commands the game can send back

`POST /cmd` allowlist only (no arbitrary shell):
`forge_ticket` (runs `prompt_compiler.py --draft` for a GH issue),
`laya_guard` (runs `laya_cli.py predict --preset guard`),
`compact_hint`, `refresh_repo`. WS frames: `order`, `gate_answer`,
`cmd`, `set`, `ping`. Everything else lands as intent files for the
orchestrator to approve.

## Troubleshooting

- Dark/empty scene: check the on-page `#booterr` overlay (top-left) or
  `curl http://127.0.0.1:8798/health`.
- No telemetry: confirm `events.jsonl` grows (`tail -1`), then check
  `repo_tick`/`tail_loop` logs; offline emission still lands via path 2.
- Port clash with rtsd: agent-rts defaults to 8798; rtsd stays on 8797.
