---
name: mcp-lazy-enablement
description: Use when deciding which MCP servers to keep active, when context feels bloated from unused MCP tools, when a task only needs one MCP server temporarily, or when auditing which servers to enable/disable per task. Guides selective MCP enablement to minimize context-window tax.
---

# MCP Lazy Enablement

## Why

Every MCP server injects **all its tool definitions** into the system prompt
of every conversation — even when you don't use those tools. Two servers can
eat a third of a 200K window before the first user message (Matt Pocock,
"Context Windows Explained for Coding Agents"). The `mcp-context-audit` skill
measures the cost; this skill guides **when to enable and disable** servers
to keep that cost minimal.

**Principle:** MCP servers should be active only when a task needs them.
Default state: minimal or zero MCP servers. Enable on demand; disable when
the task is done.

## When to Use

- Deciding which MCP servers to keep in `mcp_config.json` vs remove.
- A task needs one MCP server temporarily (e.g. Jira for a ticket update).
- Context feels bloated and MCP tool definitions are suspected.
- Setting up a new project and choosing which MCP servers to configure.
- After `mcp-context-audit` flags a server as too expensive.

## When NOT to Use

- No MCP servers configured — nothing to manage.
- You use one MCP server constantly and its cost is justified — leave it.

## Workflow

### Step 1: Audit current MCP cost

```
exec: python3 "{{APPDATA}}/devin/scripts/context-budget.py" --full
```

This shows the token cost of MCP overhead alongside `.devin/global_rules.md` and skills.

### Step 2: Classify each server

| Classification | Criteria | Action |
|---|---|---|
| **Always-on** | Used in >50% of sessions, cost <3% of window | Keep in `mcp_config.json` |
| **On-demand** | Used for specific task types (Jira, database, deploy) | Enable only for those tasks |
| **Rarely used** | Used in <10% of sessions | Remove; re-add when needed |
| **Never used** | Configured but never invoked | Remove immediately |

### Step 3: Enable/disable per task

**To disable a server temporarily** (without removing config):
1. Move the server entry from `mcp_config.json` to a backup file
   (e.g. `mcp_config.disabled.json`)
2. Restart the session — the server's tools no longer load
3. When the task needs it, move it back and restart

**For plugin-format installs:** use `devin plugins info <name>` to see
which MCP servers a plugin provides. If a plugin's MCP servers are too
expensive for the current task, consider whether the plugin is needed.

### Step 4: Verify the savings

After disabling, re-run the audit:

```
exec: python3 "{{APPDATA}}/devin/scripts/context-budget.py" --full
```

Confirm the MCP overhead dropped. The freed tokens go to actual work.

## Decision Heuristic

```
Task starts → check: does this task need MCP tools?
  NO  → ensure no MCP servers are active (minimal context)
  YES → enable ONLY the server(s) this task needs
        → run mcp-context-audit to verify cost
        → do the work
        → disable when task is done
```

## Anti-Patterns

- **Keeping all MCP servers always-on "just in case."** Permanent context
  tax for speculative use. This is the #1 cause of MCP bloat.
- **Never auditing MCP cost.** Servers grow tools over time. Re-audit
  periodically with `mcp-context-audit` and `context-budget.py --full`.
- **Adding MCP servers without measuring.** Always measure before and after
  with `context-budget.py --full`.
- **Treating MCP config as immutable.** It's a living config. Enable and
  disable as tasks change.
- **Ignoring tool count per server.** >10-15 tools per server degrades
  tool-selection accuracy below 90% (arXiv:2606.30317). Prefer narrower
  servers or scoped tools.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `mcp-context-audit` | Measures per-server token cost. Run before this skill. |
| `context-window-hygiene` | General context management. This skill is the MCP-specific layer. |
| `context-budget.py --full` | Reports MCP overhead as part of total fixed context cost. |
| `context-pressure.py` | Tracks live context growth; MCP overhead is part of the fixed cost. |

## Source

- MCP bloat: "Context Windows Explained for Coding Agents" (Matt Pocock,
  AI Hero) — "I tend to be extremely, extremely cautious about adding MCP
  servers to my setup because I know how important having a lean context
  window is."
- Tool-count accuracy threshold: arXiv:2606.30317 (<10-15 tools/server for
  >90% selection accuracy).
- Context budget measurement: `context-budget.py --full` (this bundle).
