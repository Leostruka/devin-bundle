# api-bridge

OpenAI-compatible local API over the devin CLI (issue #478).

Devin exposes non-standard surfaces (`acp` stdio, `-p` print, cloud
sessions). Harnesses like opencode/hermes expect the conventional
chat-completions API. `bridge.py` translates between them and serves
on localhost or the LAN.

```bash
python extensions/api-bridge/bridge.py serve --port 8787          # loopback
python extensions/api-bridge/bridge.py serve --bind 0.0.0.0 \
    --token SHARED_SECRET                                          # LAN (auth required)
```

Options: `--port`, `--bind`, `--token`, `--devin` (CLI path),
`--workdir` (isolated cwd for prompts), `--timeout` (s, default 300),
`--concurrency` (max parallel backend calls, default 2 — extras queue).
`--backend acp` upgrades the backend to a warm `devin acp` process:
`stream:true` then yields REAL incremental deltas and responses carry
real token usage (verified live: chunks arrive as the agent generates).
One process = serialized prompts; a fresh `session/new` per request
keeps the OpenAI contract stateless.

Endpoints:

- `POST /v1/chat/completions` — `{model, messages[], stream}`; each
  request spawns `devin -p` in an isolated `--workdir` so repo
  context does not bleed in. `stream:true` emits one delta + `[DONE]`
  (devin -p flushes once — no fake token chunks). `model` validated
  against the inventory; `"devin"` works as a compatibility alias.
- `GET /v1/models` — parsed from `devin models` at startup.
- `GET /` — self-describing surface (endpoints, model count, cap).
- `GET /health` — liveness.

Errors are OpenAI-shaped (`{"error": {message, type, param}}`):
400 invalid request / unknown model, 401 unauthorized, 502 upstream
or model failure, 504 backend timeout.

Unsupported generation params (`temperature`, `max_tokens`, `stop`,
`tools`, …) are accepted for client compatibility but surfaced
verbatim in the response `x-ignored-params` field — never silently
dropped.

CORS: `OPTIONS` preflight handled; `Access-Control-Allow-Origin`
echoes the request `Origin` (loopback/LAN data stays local — no
cross-network exposure added).

Consume from a harness, e.g.:

```bash
opencode --model local/devin --base-url http://127.0.0.1:8787/v1
```

Limits: devin is an agent, not a raw model — latencies are seconds,
not milliseconds; `usage` token counts are ~4-chars/token estimates
(no token surface on `-p`); multi-turn is flattened into a
transcript prompt. `cli` mode is honest about flushing once;
`--backend acp` (#489) delivers real incremental SSE + real usage.
Conversation-keyed session reuse remains deferred (#478).
