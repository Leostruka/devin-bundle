---
name: agent-cost-guard
description: Use when monitoring token cost per loop, detecting token maxing, or limiting parallel subagents to control cost and context pressure.
---

# Agent Cost Guard

Monitors token cost and agent parallelism to prevent runaway spending. Enforces the 1-3 subagent limit and alerts when a loop or task is consuming excessive tokens.

## When to use

- When a task involves loops, retries, or polling.
- When multiple subagents are being dispatched.
- When the conversation is long and context is tight.
- When the user asks about cost or token usage.

## Limits

| Limit | Action |
|-------|--------|
| 1-3 subagents | Default maximum. Alert if more are requested. |
| >3 subagents | Require explicit user approval. |
| Token maxing | Detect when effort is disproportionate to task difficulty. |
| Loop cost | Bound retries and polling; each iteration multiplies cost. |

## What to check

1. **Subagent count.** Are more than 3 subagents being dispatched at once? The PreToolUse hook `scripts/validate-tool-args.py` enforces `run_subagent` `max_parallel <= 3` and requires `max_parallel` to be an integer.
2. **Loop bounds.** Are retries, polling, or verification loops bounded?
3. **Token cost.** Is the effort level appropriate for the task difficulty?
4. **Context pressure.** Is the active context approaching the threshold?

## Process

```
Before dispatching subagents or starting a loop
  → Check subagent count (limit: 3)
  → Check loop bounds (max retries, max polls)
  → Check effort level (match to task difficulty)
  → If any limit exceeded: alert user or split into batches
```

## Example

```python
# Bad: unbounded retry loop
while not success:
    retry()  # costs tokens each iteration

# Good: bounded retry with max attempts
for attempt in range(3):
    if success:
        break
    retry()
```

## Anti-patterns

- Dispatching >3 subagents without approval.
- Unbounded retry or polling loops.
- Using maximum effort for trivial tasks.
- Ignoring token cost when the parent model is paid.

## Cross-skills

- `effort-calibration` — chooses the right effort level for the task.
- `cost-optimization` — broader cost guidance (models, cache, MCPs).
- `context-window-hygiene` — context pressure and clear/compact decisions.
- `dispatching-parallel-agents` — parallel work, but bounded by this guard.
