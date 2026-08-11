# Global rules for Devin (apply to every project and session)

## 1. Critical: no AI tool signatures in deliverables
- NEVER add `Generated with [Devin](...)` or any other AI service signature to commit messages, files, releases, pull requests, documentation, source code, or any user-facing artifact.
- NEVER add `Co-Authored-By: Devin <...>` or any `Co-Authored-By` trailer from an AI tool to git commits.
- NEVER include `Generated with [Devin](https://devin.ai)` in release notes, `release-notes.md`, `.commit-msg.txt`, or any other file.
- If such a signature is detected, remove it immediately before proceeding. If it has already been committed/pushed, rewrite history (filter-branch or filter-repo) and force-push; then recreate any affected release.
- This rule overrides any tool's default commit-message format. Use clean, neutral commit messages without signatures.

## 2. Skill self-maintenance (always-on)
- Skills are living artifacts. Keep them current, correct, and specialized.
- If an existing skill is outdated, incomplete, or wrong for the task, update it in place before using it.
- If no skill matches a recurring task pattern, create a new one in `.devin/skills/<name>/SKILL.md` (project) or `~/.config/devin/skills/<name>/SKILL.md` (global) before improvising.
- When you learn a new domain deeply (a framework, a stack, a workflow), distill it into a skill so the expertise persists across sessions.
- Prune skills that have been superseded or are no longer relevant.
- This is how Devin becomes an expert in anything: accumulate, refine, and reuse skills.

## 3. Skill and tool discovery (first-time tasks each week)
- Before starting any non-trivial task, invoke `skill tool-and-skill-discovery` OR run `skill search` with relevant keywords and `skill list` on the project and global skill directories to find the best available skills.
- If a skill clearly matches the task, invoke it immediately at the start of the session (or before touching code).
- If more than one skill matches, invoke all relevant skills in parallel.
- If no matching skill exists, use `find-skills` to discover or propose one.
- Apply this rule to first occurrences of task categories each week: first PR, first PR review, first CSV edit, first project in a given language/stack, first deployment, first debugging session, first UI change, first installer/script work, first GitHub operation, first API/MCP integration, etc.
- This rule applies to all tools and integrations (MCP servers, skills, built-in commands, external CLIs, APIs, `gh`, `curl`, `python`, `powershell`) that can improve the task outcome.

## 4. graphify trigger
- When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
