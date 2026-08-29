---
name: cost-optimization
description: Use when the user wants to reduce token, compute, or infrastructure costs. Covers context window budget, MCP selection, caching, model routing, and query optimization.
triggers: [user, model]
---

# Cost Optimization

Reduce token, compute, and infrastructure spend.

## When to use

- Token bills are high.
- Need to choose a cheaper model for a subtask.
- MCP servers are bloating context.
- Caching or routing can save cost.

## Core protocol

1. **Measure current cost.** Tokens per request, model tier, cache hit rate.
2. **Audit context usage.** Use `mcp-context-audit` to find heavy MCP tool definitions.
3. **Right-size models.** Use `swe-1-7` for subagents and `glm-5-2` for the free primary model; use paid models only when explicitly approved.
4. **Add caching.** Reuse previous tool outputs and summaries where safe.
5. **Shorten prompts.** Remove unused context, prefer file snippets over full reads.
6. **Re-measure.** Compare cost before and after.

## See also

- `mcp-context-audit` — MCP server context-window cost.
- `cost-optimization` — general token, compute, and infrastructure spend.

## Output rule

- Report tokens/cost before and after, and the commands used to measure.
