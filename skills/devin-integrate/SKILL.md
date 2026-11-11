---
name: devin-integrate
description: Use when embedding the Devin agent into an external surface — a device (Busy Bar), an LLM harness (opencode/hermes), a service, an IDE, or a cron. Covers direction (devin-as-callee vs caller vs bidirectional), the transport ladder, the verified surface inventory, and the integration contract checklist. Complements cli-adapter (outbound agent->app); this skill is inbound/integration.
triggers: [user, model]
allowed-tools: [read, grep, find_file_by_name, write, edit, exec, webfetch]
---

# devin-integrate

Embed Devin into an arbitrary surface. Origin case: Busy Bar reel
(huwprosser/DfXwuL0izsO) — agent sees a new device, looks up its API,
and builds. This skill is that loop, codified.

## Step 1 — direction

| Direction | Meaning | Examples |
|---|---|---|
| callee | something calls devin | harness, device button, cron, CI step |
| caller | devin calls something | hooks, MCP tools, push wrappers |
| bidirectional | both, same session | ACP sessions, WS stream + push |

## Step 2 — transport ladder (pick the cheapest)

`file ledger` < `subprocess stdout` < `HTTP` < `stdio JSON-RPC` < `WebSocket`

- Ledger/file: dumb consumers, state push. Ref: `scripts/focus.py` ->
  `.devin/ledgers/focus.jsonl` -> `extensions/busybar/push.py`.
- Subprocess: `devin -p` prompt->text on stdout. Ref: api-bridge backend.
- HTTP: OpenAI-compatible surface. Ref: `extensions/api-bridge/bridge.py`
  (`/v1/chat/completions`, `/v1/models`, `/health`, `GET /`; LAN binds
  require `--token`).
- stdio JSON-RPC: sessions + streamed chunks + client-gated fs.
  Ref: `.devin/scratch/acp-spike/client.py` (`initialize` ->
  `session/new` -> `session/prompt` -> `agent_message_chunk`;
  MUST answer `fs/read_text_file` or the agent deadlocks in ask/plan).
- WebSocket: device state streams. Ref: Busy Bar `StateStream`
  (docs.busy.app/bar/dev/http-api) — input events -> agent triggers.

## Verified surface inventory (CLI 3000.12.43)

| Surface | Dir | Notes |
|---|---|---|
| `devin -p` | callee | full agent run, seconds latency, stdout text |
| `devin acp [--agent-type]` | bidir | summarizer/review/codemap agents verified; default agent heavy |
| api-bridge | callee | OpenAI-compat; `x-ignored-params` honest field; usage = ~4ch/tok estimate |
| hooks | caller | `tool_response.overflow_path` exists on truncation (12.17+) |
| `devin cloud/forward` | callee | org API; DRS needs entitlement; forward=tunnel ports |
| busybar push | caller | `display/draw`+`display/clear`, USB no-auth, LAN token |

## Playbook (working examples in-repo)

1. `extensions/api-bridge/bridge.py` — full callee integration.
2. `extensions/busybar/push.py` — minimal caller: 2 endpoints, fail-soft.
3. `extensions/gcal/wrapper.py` — service adapter, ok-envelope contract.
4. `.devin/scratch/acp-spike/client.py` — bidirectional session client.
5. `scripts/focus.py` — ledger emitter, zero-dep integration surface.

## Contract checklist (every integration)

- Auth boundary explicit: loopback free, LAN requires token (bridge
  refuses off-loopback without `--token`).
- Fail-soft: unreachable surface -> stderr note + exit 0 for advisory
  pushes; hard fail only when the surface IS the deliverable.
- `{"ok": false}` envelopes exit non-zero (audit check [36]).
- UTF-8 pinned: subprocess `encoding="utf-8", errors="replace"`;
  file I/O `encoding="utf-8"` (audit [37]/[38]).
- No fake streaming: if the backend flushes once, emit one delta +
  `[DONE]` — never fabricate token chunks.
- Verify live once with a real call before claiming integration works;
  hardware-blocked surfaces get spec + skeleton + mock tests.

## Anti-patterns

- Assuming device/harness has auth off by default (LAN busybar needs token).
- Silently dropping unsupported request params — surface them
  (`x-ignored-params` pattern in bridge).
- Spawning unbounded devin processes under concurrent callers — cap
  (bridge `--concurrency` semaphore).
