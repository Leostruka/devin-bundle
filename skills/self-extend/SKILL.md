---
name: self-extend
description: Use when evolving the agent's own capabilities with a new skill, custom subagent, plugin, hook, MCP server, or project rule.
---
# Self-Extension

## Overview

Extend Devin CLI's behavior by adding files to the project (`./.devin/`) or to your global Devin config (`~/.config/devin/` on Linux/macOS, `%APPDATA%\devin\` on Windows). Most changes are picked up at the next session or skill reload.

## What to create for each need

| I want to... | Create | Location | Hot-reload |
|---|---|---|---|
| Add a reusable workflow the agent can invoke | Skill | `.devin/skills/<name>/SKILL.md` (project) or `~/.config/devin/skills/<name>/SKILL.md` (global) | next `skill list` / session |
| Define a specialized worker for a task type | Custom subagent profile | `.devin/agents/<name>.md` or `.devin/agents/<name>/AGENT.md` (project/global `~/.config/devin/agents/`) | next session |
| Add always-on context for a project or globally | Rules | `AGENTS.md` (project root or `~/.config/devin/AGENTS.md`) or `.devin/global_rules.md` or `.devin/rules/*.md` | session start |
| Run custom logic at lifecycle events | Hooks | `.devin/hooks.v1.json` or `.devin/hooks.json` | next session |
| Give the agent new API/database tools | MCP server | `.devin/mcp_config.json` or `~/.config/devin/mcp_config.json` | next session |
| Bundle skills/rules/hooks/MCP for distribution | Plugin | `.devin-plugin/plugin.json` manifest + skills/rules/hooks/mcp | install/reload |

## Creating skills

Project skill (committed to repo):

```markdown
---
name: my-skill
description: Use when [specific triggering conditions]
---

# My Skill

## Overview
...
```

Save as `.devin/skills/my-skill/SKILL.md`. For personal skills, use `~/.config/devin/skills/my-skill/SKILL.md` (or `%APPDATA%\devin\skills\my-skill\SKILL.md` on Windows).

Skill frontmatter can also set:

- `allowed-tools`: restrict which tools the skill can use (e.g. `[read, grep, glob, exec]`)
- `subagent: true`: run the skill as a `subagent_general` subagent
- `agent: <profile>`: run the skill as a specific custom subagent
- `model`: override the model for this skill (e.g. `swe-1-7` [free], `sonnet` [paid])
- `permissions`: add permission grants/restrictions (e.g. `allow: [Read(src/**)]`, `deny: [exec]`)
- `triggers`: who can invoke it (default `[user, model]`)

Discover with `skill list --path .` and `skill search --path . --keywords "..."`. Invoke with `/my-skill`.

## Creating custom subagents

Custom subagents are Devin CLI profiles that specialize in a kind of work (e.g. `reviewer`, `researcher`).

Profile definition in `.devin/agents/reviewer.md` or `.devin/agents/reviewer/AGENT.md`:

```markdown
---
name: reviewer
---

You are a careful code reviewer. Read the diff, then report only concrete issues with file paths and line numbers.
```

Reference the profile in a skill frontmatter:

```yaml
---
name: review-pr
description: Use when the user asks for a focused PR review.
agent: reviewer
---
```

Or dispatch directly from a skill:

```
Run a `subagent_general` or `subagent_explore` subagent with the reviewer profile, passing the diff and the review checklist.
```

## Adding rules

`AGENTS.md` at the project root (or `~/.config/devin/AGENTS.md` globally) is always loaded. Keep it small; put detailed guidance in skills.

`.devin/rules/*.md` files can have `trigger` frontmatter (`always_on`, `manual`, `model_decision`, `agent`, `glob`) to load only when relevant.

`.devin/global_rules.md` is an always-on file inside `.devin/`.

## Adding hooks

Hooks run custom logic at session lifecycle events. Place them in `.devin/hooks.v1.json` or `.devin/hooks.json`.

Common events:

| Event | Use |
|---|---|
| `PreToolUse` | Inspect or block a tool call |
| `PostToolUse` | Log or modify tool output |
| `PermissionRequest` | Auto-allow/deny specific permission patterns |
| `UserPromptSubmit` | Inject context when the user sends a message |
| `Stop` | Run cleanup before the agent stops |
| `SessionStart` / `SessionEnd` | Setup/teardown |

Example `.devin/hooks.v1.json`:

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": "exec",
      "type": "command",
      "command": "echo 'exec called: {{tool_name}}' >> .devin/audit.log"
    }
  ]
}
```

## Adding MCP servers

MCP servers give the agent new tools. Configure them in `.devin/mcp_config.json` (project) or `~/.config/devin/mcp_config.json` (global):

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { }
    }
  }
}
```

For secrets, use `.devin/mcp_config.local.json` (gitignored).

## Packaging as a plugin

A plugin is a directory with a `.devin-plugin/plugin.json` manifest. It can ship:

- `skills/<name>/SKILL.md`
- `AGENTS.md`
- `rules/*.md`
- `agents/<name>.md`
- `mcp_config.json`
- `hooks.json`/`hooks.v1.json`

Plugins can be installed from a GitHub repo, git URL, or local folder when Devin CLI plugin support is enabled. See the Devin CLI docs for `plugin.json` format.

## Helper scripts

If a skill needs executable helpers, keep them in the skill's `scripts/` directory. Use Python for cross-platform work, Bash for one-off shell integration, or JavaScript if the helper is tool-specific. Document dependencies and exit codes.

## Constraints

- Do not ask users for secrets; put credentials in `.devin/config.local.json` or env vars.
- Do not modify repository security policies or CI compliance settings.
- Keep `AGENTS.md` small; prefer skills for detailed guidance.
- Prefer standard Devin CLI paths; do not reference non-Devin runtimes.

## Dynamic Subagent Construction (AOrchestra 4-tuple)

Any subagent can be described as a 4-tuple: **⟨Instruction, Context, Tools, Model⟩**.
The 7 fixed profiles (architect, debugger, implementer, researcher, reviewer,
subagent_explore, subagent_general) are pre-configured 4-tuples. For task-specific
specialization, override individual tuple elements instead of creating a new profile:

| Element | What it controls | When to override |
|---|---|---|
| **Instruction** | What the subagent must accomplish | Task needs a specific goal not covered by any profile |
| **Context** | Task-relevant working memory | Task needs scoped context (filter out irrelevant files/history) |
| **Tools** | Actions the subagent can take | Task needs restricted tool access (e.g., read-only exploration) |
| **Model** | Which LLM executes | Cost-performance trade-off (cheaper model for simple subtasks) |

**How to apply:** When dispatching via `run_subagent`, specify `task` (instruction),
`profile` (defaults for context/tools/model), and override with task-specific
constraints in the `task` text. The 7 profiles remain as backward-compatible defaults.

**Source:** AOrchestra (ICML 2026, arXiv:2602.03786). "Sub-agents should be treated
as recipes created at runtime, not fixed roles." Training-free mode: 16.28% relative
improvement over baselines. SFT mode: +11.51% pass@1 on GAIA (requires 2K trajectories).
