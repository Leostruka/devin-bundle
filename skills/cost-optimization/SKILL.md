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

## Context and loop cost controls

- **Subagents first.** Delegate heavy exploration to `swe-1-7` subagents; keep the main context lean.
- **Token limit.** Use `tokens-limit` or equivalent budget guard when available; stop if the threshold is exceeded.
- **Clear vs compact.** Default to `clear` between unrelated tasks; `compact` only when continuity is required. Compaction is lossy.
- **Parallelism.** Limit concurrent subagents to 1-3. If a task suggests more than 3, alert the user and ask for approval.
- **Loops cost money.** Every loop iteration increases token count. Cap retries, bounded loops, and unnecessary polling.

## See also

- `mcp-context-audit` — MCP server context-window cost.
- `context-window-hygiene` — context-window management and `clear`/`compact` decisions.
- `cost-optimization` — general token, compute, and infrastructure spend.

## Output rule

- Report tokens/cost before and after, and the commands used to measure.
