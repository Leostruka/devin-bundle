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

Endpoints:

- `POST /v1/chat/completions` — `{model, messages[], stream}`; each
  request spawns `devin -p` in an isolated `--workdir` so repo
  context does not bleed in. `stream:true` emits one delta + `[DONE]`
  (devin -p flushes once — no fake token chunks).
- `GET /v1/models` — parsed from `devin models` at startup.
- `GET /health` — liveness.

Consume from a harness, e.g.:

```bash
opencode --model local/devin --base-url http://127.0.0.1:8787/v1
```

Limits: devin is an agent, not a raw model — latencies are seconds,
not milliseconds; `usage` token counts are 0 (no token surface on
`-p`); multi-turn is flattened into a transcript prompt.
