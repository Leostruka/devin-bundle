---
name: tool-and-skill-discovery
description: Use when the user asks how to do something, needs the right skill or tool, no skill seems to match the task, or wants to discover, install, or evaluate a new skill for Devin CLI.
---
# Tool and Skill Discovery

## When to use
- At the start of any non-trivial task.
- When unsure which skill, MCP server, CLI, or built-in tool is best.
- When encountering a new task category (first PR, first CSV edit, first
  deployment, first UI change, first installer work, first API integration).
- When the user says "find a skill for X" or "is there a skill for X".
- When the user wants to install or evaluate a new skill.

## What to do

### 1. List available skills
- `skill list --path <project>`
- `skill list --path ~/.config/devin`
- `skill list --path %APPDATA%\devin\skills` (Windows)
- `skill list --path ~/.agents/skills`

### 2. Search for relevant skills
- `skill search --path <project> --keywords "<keyword1> <keyword2>"`
- `skill search --path ~/.config/devin --keywords "<keyword1> <keyword2>"`

### 3. Check available MCP servers
- `mcp_list_servers`
- `mcp_list_tools --server_name <server>`

### 4. Check built-in tools that can help
- `web_search` for external docs/examples.
- `webfetch` for specific pages.
- `mcp_call_tool` for integrated services.
- `run_subagent` for parallel exploration.

### 5. Invoke matching skills immediately
- If one or more skills match, invoke them before touching code.
- If multiple skills match, invoke them in parallel.

### 6. If no skill matches — search externally and evaluate

**Search known skill repositories:**
- `github:Leostruka/devin-bundle` — this bundle
- `gh search repos <keyword> skills` or `web_search` for more

**Evaluate before recommending:**
1. **Relevance** — does the README describe the task?
2. **Compatibility** — uses Devin CLI patterns (`run_subagent`, `skill list`,
   `.devin/skills/`)? If it references non-Devin AI tools or paths, it needs
   adaptation.
3. **Quality signals** — recent commits, tests, clear examples, no hardcoded
   secrets.

**Install:**
```bash
# Clone to the global Devin skills directory
git clone https://github.com/<owner>/<repo>.git ~/.config/devin/skills/<name>

# Or into a project
mkdir -p .devin/skills/<name>
# copy SKILL.md and supporting files
```

Verify it appears:
```bash
skill list --path ~/.config/devin
```

**Adapt if necessary:**
1. Replace non-Devin tool names with Devin CLI equivalents.
2. Update file paths to `~/.config/devin/skills/` or `.devin/skills/`.
3. Convert bash scripts to Python if the skill bundles helpers.
4. Remove platform-specific frontmatter.

### 7. If no skill is found anywhere
1. Acknowledge that no existing skill was found.
2. Offer to help directly with the task.
3. Suggest creating a minimal skill in `.devin/skills/<name>/SKILL.md` if the
   task is recurring.

## Tool categories and typical integrations

| Task category | Tools/skills to consider |
|---------------|--------------------------|
| Git / PR      | `git-helper`, `gh`, `code-review`, `receiving-code-review` |
| GitHub ops    | `gh`, `mcp_call_tool` for GitHub MCP, `web_search` |
| CSV / data    | `python` (pandas), `powershell` `Import-Csv`, `grep` |
| Debugging     | `diagnosing-bugs`, `tdd` |
| Verification  | `verification-before-completion` |
| Documentation | `context7`, `web_search`, `webfetch` |
| Planning      | `writing-plans`, `executing-plans`, `planning-pipeline`, `wayfinder` |
| Context mgt   | `context-folding`, `context-window-hygiene`, `mcp-context-audit` |

## Creating or updating a skill
- If an existing skill is wrong or incomplete, update it first.
- If a new pattern emerges, create a minimal skill:
  - Directory: `.devin/skills/<name>/` (project) or `~/.config/devin/skills/<name>/` (global)
  - File: `SKILL.md`
  - Content: when to use, what to do, example commands, common pitfalls.

## Output
- Return a short summary of which skill(s) or tool(s) were selected and why.
- If no good match exists, state that and propose next step.
