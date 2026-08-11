---
name: find-skills
description: "Use when the user wants to discover, install, or evaluate a new skill for Devin CLI."
---

# Find Skills

Help the user discover and install skills for Devin CLI.

## When to use this skill

- The user asks "how do I do X" and no skill in the current bundle matches.
- The user says "find a skill for X" or "is there a skill for X".
- The user wants to install a new skill from a repository.
- The user wants to evaluate an existing skill against a task.

## Where Devin CLI looks for skills

1. **Project skills** — `.devin/skills/<name>/SKILL.md`
2. **Global user skills** — `~/.config/devin/skills/<name>/SKILL.md` (Linux/macOS) or `%APPDATA%\devin\skills\<name>\SKILL.md` (Windows)
3. **Cross-runtime skills** — `.agents/skills/<name>/SKILL.md`
4. **Built-in skill discovery** — `skill list --path <dir>` and `skill search --path <dir> --keywords "..."`

## How to help users find skills

### Step 1 — Understand the need

- Domain (e.g., testing, deployment, UI, documentation)
- Specific task (e.g., "review PRs", "create animations", "mutation test")
- Whether this is a recurring task that justifies a skill

### Step 2 — Search the current bundle first

Use `skill list --path <project>` and `skill search --path <project> --keywords "<keyword>"` to see if a matching skill already exists in the project or global Devin skills directory.

Examples:

- "find a skill for PR review" → `skill search --path . --keywords "review code pr"`
- "how do I mutation test?" → `skill search --path ~/.config/devin --keywords "mutation test"`

### Step 3 — Search for external skills

If the bundle does not have a match, search known skill repositories on GitHub. Good starting points:

- `github:obra/superpowers` — generalist skills
- `github:Leostruka/devin-bundle` — this bundle
- `github:anthropics/skills` — Anthropic skills
- `github:vercel-labs/agent-skills` — Vercel skills

Use `gh search repos <keyword> skills` or `web_search` to find more.

### Step 4 — Evaluate before recommending

Before installing or using an external skill, verify:

1. **Relevance** — does the README describe the task the user asked about?
2. **Compatibility** — does the skill use Devin CLI patterns (`run_subagent`, `skill list`, `.devin/skills/`)? If it references Claude Code, Codex CLI, or Gemini CLI paths, it will need adaptation.
3. **Quality signals** — recent commits, tests, clear examples, and no hardcoded secrets.

### Step 5 — Install the skill

If the skill is a GitHub repository, install it into the global Devin skills directory:

```bash
# Clone to the global Devin skills directory
git clone https://github.com/<owner>/<repo>.git ~/.config/devin/skills/<name>

# Or into a project
mkdir -p .devin/skills/<name>
# copy SKILL.md and supporting files
```

Then verify it appears:

```bash
skill list --path ~/.config/devin
```

### Step 6 — Adapt if necessary

If the skill is not Devin CLI native:

1. Replace non-Devin tool names with Devin CLI equivalents.
2. Update file paths to `~/.config/devin/skills/` or `.devin/skills/`.
3. Convert bash scripts to Python if the skill bundles helpers.
4. Remove platform-specific frontmatter like `disable-model-invocation` or `superpowers:`.

## When no skill is found

1. Acknowledge that no existing skill was found.
2. Offer to help directly with the task.
3. Suggest creating a minimal skill in `.devin/skills/<name>/SKILL.md` if the task is recurring.

## Output

Return a short summary of:

- Which skills were searched
- Any matching skill found
- The recommended install/adaptation steps
