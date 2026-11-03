---
name: agent-reach
description: Use when researching trends or public sources across credential-free channels (YouTube transcripts/metadata, RSS/Atom feeds). Routes to extensions/agent-reach/wrapper.py, a whitelist passthrough to the agent-reach CLI (`get` grammar). Credential/cookie channels are out of scope.
triggers: [user, model]
---

# Agent Reach

Trend and source research via `extensions/agent-reach/wrapper.py` --
thin passthrough to `agent-reach` on PATH (or `uv tool run agent-reach`).
Upstream 0.1.x reads go through `agent-reach get <channel>[.<command>]`;
channels are installable manifests with per-channel `auth` metadata.

## Scope: credential-free only

Whitelisted channels: `youtube`, `rss` (upstream index `auth:none`;
see `agent-reach list --all`).

Rejected by design (bundle credential policy -- no credentialed
scraping at the bundle boundary): `twitter`, `x`, `reddit`,
`instagram`, `xiaohongshu`, `boss`. Requests for these return
`status: rejected` with the reason; do not work around the block.

## Setup

Channels install one at a time from the upstream index (outside the
wrapper, deliberate env setup):

```bash
uv tool run agent-reach list --all      # channel index + installed state
uv tool run agent-reach install youtube # installs yt-dlp backend
uv tool run agent-reach install rss     # feedparser backend
```

## Commands

```bash
W=extensions/agent-reach/wrapper.py

python $W doctor                          # probe invoker + per-channel status
python $W youtube <query>                 # default youtube command
python $W youtube.transcript <video-id>   # transcript + metadata
python $W rss.feed <feed-url>             # feed items as clean text
python $W <channel>.<command> <query>     # any whitelisted channel.command
```

All output is JSON (`status`, `command`, `stdout`, `stderr`,
`duration_s`); missing toolchain reports `status: missing`; upstream
`get` output arrives with `--json` applied by the wrapper.

## Workflow

1. `doctor` once per session; confirm invoker + channel readiness.
2. Query whitelisted channels; positional args only, no flag passthrough.
3. Cross-check findings across two channels before citing.

## Composition

- `research` skill: synthesize wrapper output into cited findings.
- `social-midia`: when the task is publishing/monitoring rather than
  source gathering; keep credentialed actions there, not here.

## Boundaries

- Credential-free channels only; rejection is policy, not a bug.
- No flags forwarded to the CLI; positional args only (the wrapper adds
  `--json` itself for deterministic output).
- Output bounded at 1 MiB per stream; 120s timeout.
