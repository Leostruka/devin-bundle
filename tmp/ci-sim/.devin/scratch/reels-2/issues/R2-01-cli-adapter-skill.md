# cli-adapter: no MCP -> agent builds the CLI itself

status: resolved
priority: P2
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 01 (catlabs): when no MCP or official connector exists, the agent is told to build a CLI tool that drives the app (full DAW control). Transcript: `.devin/scratch/reels-2/transcripts/01-catlabs.json`.
Bundle precedent: `extensions/agent-reach/wrapper.py` is exactly this pattern (whitelist CLI passthrough). `mcp-governance` covers MCP selection; nothing covers the "no MCP exists" branch.

## Recommendation
New skill `skills/cli-adapter/SKILL.md`: decision tree (official MCP -> use it; none -> inspect tool's CLI/API surface; build a thin wrapper script under `.devin/tools/` or `extensions/`; whitelist args; smoke-test read-only calls first; document the adapter in the skill output). Cites agent-reach/wrapper.py as the reference implementation. Include the "describe the change, agent controls the app" UX pattern and the cyber-risk caveat (a CLI that can mutate app state needs the destructive-ops guardrails).

## Verification
`ls skills/cli-adapter/SKILL.md`; manifest + count bump; audit.py clean.

## Answer

`skills/cli-adapter/SKILL.md` - decision order (MCP -> wrap CLI -> thin API CLI -> computer-use), wrapper contract (list-form, verb whitelist, JSON envelope, missing->status), smoke-test rule, DAW liability note; cites `extensions/agent-reach/wrapper.py`.
