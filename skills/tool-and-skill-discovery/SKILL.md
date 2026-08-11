---
name: tool-and-skill-discovery
description: Use when the user asks how to do something, needs the right skill or tool, or no skill seems to match the task.
---
# Tool and Skill Discovery

## When to use
- At the start of any non-trivial task.
- When you are unsure which skill, MCP server, CLI, or built-in tool is best for the job.
- When you encounter a new task category (first PR, first CSV edit, first deployment, first UI change, first installer work, first API integration, etc.).

## What to do
1. **List available skills**
   - `skill list --path <project>`
   - `skill list --path ~/.config/devin`
   - `skill list --path %APPDATA%\devin\skills` (Windows)
   - `skill list --path ~/.agents/skills`

2. **Search for relevant skills**
   - `skill search --path <project> --keywords "<keyword1> <keyword2>"`
   - `skill search --path C:\Users\<user> --keywords "<keyword1> <keyword2>"`

3. **Check available MCP servers**
   - `mcp_list_servers`
   - `mcp_list_tools --server_name <server>`

4. **Check built-in tools that can help**
   - `web_search` for external docs/examples.
   - `webfetch` for specific pages.
   - `mcp_call_tool` for integrated services.
   - `run_subagent` for parallel exploration.

5. **Invoke matching skills immediately**
   - If one or more skills match, invoke them before touching code.
   - If multiple skills match, invoke them in parallel.

6. **If no skill matches**
   - Use `find-skills` to ask for help discovering or installing one.
   - Consider creating a new skill in `.devin/skills/<name>/SKILL.md` (project) or `~/.config/devin/skills/<name>/SKILL.md` (global).

## Tool categories and typical integrations

| Task category | Tools/skills to consider |
|---------------|--------------------------|
| Git / PR      | `git-helper`, `gh`, `skill code-review`, `skill receiving-code-review` |
| GitHub ops    | `gh`, `mcp_call_tool` for GitHub MCP, `web_search` |
| CSV / data    | `python` (pandas), `powershell` `Import-Csv`, `grep` |
| .NET / C#     | `dotnet build`, `dotnet test`, `skill xaml-patterns`, `skill avalonia-pro-max` |
| Laravel / PHP | `skill laravel-patterns`, `skill laravel-tdd`, `skill filament-pro` |
| UI / design   | `skill wa-design-desktop`, `skill avalonia-pro-max`, `skill apple-hig` |
| Installers    | `ISCC.exe`, `powershell`, `schtasks` |
| Debugging     | `skill systematic-debugging`, `skill tdd` |
| Verification  | `skill verification-before-completion`, `skill laravel-verification` |
| Documentation | `context7`, `web_search`, `webfetch` |

## Creating or updating a skill
- If an existing skill is wrong or incomplete, update it first.
- If a new pattern emerges, create a minimal skill:
  - Directory: `.devin/skills/<name>/` (project) or `~/.config/devin/skills/<name>/` (global)
  - File: `SKILL.md`
  - Content: when to use, what to do, example commands, common pitfalls.

## Output
- Return a short summary of which skill(s) or tool(s) were selected and why.
- If no good match exists, state that and propose next step.
