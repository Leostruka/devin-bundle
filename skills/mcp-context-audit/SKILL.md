---
name: mcp-context-audit
description: Use when considering adding an MCP server, when context feels bloated with tool definitions, when auditing which MCP servers consume the most context window budget, or before committing a change to mcp_config.json. Estimates per-server tool-definition token cost and flags bloat.
---

# MCP Context Audit

## Why

Every MCP server injects **all its tool definitions** into the system prompt
of every conversation. Two "plug-and-play" servers can consume a third of a
200k window before the first user message. This is the fastest way to bloat
context and trigger lost-in-the-middle. Audit before adding; keep only what
earns its tokens.

Rule of thumb: **tool count per server under 10-15** keeps tool-selection
accuracy above 90% (arXiv:2606.30317). Above that, the model picks the wrong
tool more often than not.

## When to Use

- About to add an MCP server to `mcp_config.json`.
- Context feels bloated and MCP tool definitions are suspected.
- Periodic hygiene review of configured servers.
- A server exposes many tools and you want to know the token cost.

## When NOT to Use

- No MCP servers configured — nothing to audit.
- You already know the cost and have decided to keep the server.

## Workflow

### Step 1: List configured servers

```
exec: python3 "{{APPDATA}}/devin/skills/mcp-context-audit/scripts/mcp-context-audit.py" --config mcp_config.json
```

Reads `mcp_config.json` and reports each server's transport, command/url, and
a static bloat risk (based on config complexity). No tool calls made.

### Step 2: Measure real tool counts

The script cannot call MCP tools itself. You (the agent) list tools per
server and feed the result to the script for token estimation:

```
mcp_list_tools server_name="atlassian"
```

Capture the tool list, then pipe it to the estimator:

```
exec: python3 "{{APPDATA}}/devin/skills/mcp-context-audit/scripts/mcp-context-audit.py" --tools - < tools_atlassian.json
```

Or pass a file:

```
exec: python3 "{{APPDATA}}/devin/skills/mcp-context-audit/scripts/mcp-context-audit.py" --tools tools_atlassian.json
```

The script estimates token cost of the tool definitions (chars/4 heuristic)
and flags servers over the 10-15 tool threshold.

### Step 3: Decide

| Signal | Action |
|---|---|
| Server unused in N sessions | Remove from `mcp_config.json` |
| Tool count > 15 | Prefer a narrower server, or scope tools if the server supports it |
| Token cost > 5% of window | Justify with concrete usage; else remove |
| Untrusted server | Review code/permissions first (AGENTS.md Rule 13); run in sandbox |

### Step 4: Verify after removal

Re-run Step 1 to confirm the server is gone and the budget dropped.

## Anti-Patterns

- **Adding servers "just in case."** Permanent context tax for speculative use.
- **Auditing once and never again.** Servers grow tools over time; re-audit.
- **Trusting tool count alone.** A 5-tool server with huge descriptions can
  cost more than a 15-tool server with terse ones. Check token cost.
- **Skipping the trust review.** MCP servers run with user permissions. See
  Rule 13: evaluate against the 5 architecture patterns / 4 anti-patterns
  before adding.

## Source

- Tool-count accuracy threshold: arXiv:2606.30317 (<10-15 tools/server for
  >90% selection accuracy).
- MCP architecture patterns / anti-patterns: AGENTS.md Rule 13.
- Context bloat from MCP: "Context Windows Explained for Coding Agents"
  (Matt Pocock) — MCP servers can consume a third of the window before the
  first message.
