---
name: agent-reach
description: Use when researching trends or public sources across credential-free channels (GitHub, YouTube, Bilibili, V2EX, generic web). Routes to extensions/agent-reach/wrapper.py, a whitelist passthrough to the agent-reach CLI. Credential/cookie channels are out of scope.
triggers: [user, model]
---

# Agent Reach

Trend and source research via `extensions/agent-reach/wrapper.py` --
thin passthrough to `agent-reach` on PATH (or `uv tool run agent-reach`).

## Scope: credential-free only

Whitelisted channels: `github`, `youtube`, `bilibili`, `v2ex`, `web`,
`doctor`. These need no account, cookie jar, or API key.

Rejected by design (bundle credential policy -- no credentialed
scraping at the bundle boundary): `twitter`, `x`, `reddit`,
`instagram`, `xiaohongshu`, `boss`. Requests for these return
`status: rejected` with the reason; do not work around the block.

## Commands

```bash
W=extensions/agent-reach/wrapper.py

python $W doctor                       # probe agent-reach / uv invoker
python $W github <query args>          # repos, trends, issues
python $W youtube <query args>         # videos, transcripts metadata
python $W bilibili <query args>
python $W v2ex <query args>
python $W web <url|query args>         # generic public web fetch
```

All output is JSON (`status`, `command`, `stdout`, `stderr`,
`duration_s`); missing toolchain reports `status: missing`.

## Workflow

1. `doctor` once per session; confirm invoker.
2. Query whitelisted channels; positional args only, no flag passthrough.
3. Cross-check findings across two channels before citing.

## Composition

- `research` skill: synthesize wrapper output into cited findings.
- `social-midia`: when the task is publishing/monitoring rather than
  source gathering; keep credentialed actions there, not here.

## Boundaries

- Credential-free channels only; rejection is policy, not a bug.
- No flags forwarded to the CLI; positional args only.
- Output bounded at 1 MiB per stream; 120s timeout.
