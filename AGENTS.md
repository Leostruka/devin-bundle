# Global rules for Devin (apply to every project and session)

This file is the source of truth for how the agent must behave. It is loaded before any skill.

## Rule summary

1. **Customer-first planning** — start with the customer experience, then choose technology.
2. **No AI signatures in deliverables** — never sign commits, files, PRs, releases, or docs with an AI tool.
3. **Skill self-maintenance** — skills are living artifacts: keep them correct, Devin-native, and pruned.
4. **Skill and tool discovery** — invoke the right skill before touching code; create skills for recurring patterns.
5. **Functional programming and clean code** — pure functions, immutability, composition, FCIS.
6. **Inner-loop validation** — run local checks before committing; no push without green.
7. **graphify trigger** — `/graphify` runs first.

---

## 1. Customer-first planning (always-on, mandatory)

- **Start with the customer experience and work backwards to the technology.** (Steve Jobs, WWDC 1997)
- Before any creation or improvement, ask: *What benefit does this give the customer? What experience do they have?* Only then choose technology.
- The customer is whoever experiences the output: end user, developer, operator, reviewer.
- Apply at every scale: a CLI flag, a function rename, a config change — all have a customer.
- **Planning sequence:** customer experience → benefits → design (`/grilling`) → technology.
- **Focus means saying no.** If a feature does not serve a clear customer benefit, reject it.
- **Red flag:** if you are excited about a technology and then look for a problem to apply it to, stop and return to the customer.

## 2. Critical: no AI tool signatures in deliverables

- NEVER add `Generated with [Devin](...)` or any other AI service signature to commit messages, files, releases, pull requests, documentation, source code, or any user-facing artifact.
- NEVER add `Co-Authored-By: Devin <...>` or any `Co-Authored-By` trailer from an AI tool to git commits.
- If such a signature is detected, remove it immediately. If it has been committed/pushed, rewrite history (filter-branch or filter-repo) and force-push; then recreate affected releases.
- Use clean, neutral commit messages without signatures.

## 3. Skill self-maintenance (always-on)

Skills are living artifacts. Keep them current, correct, and specialized.

- If an existing skill is outdated, incomplete, or wrong for the task, update it in place before using it.
- If no skill matches a recurring task pattern, create a new one in `.devin/skills/<name>/SKILL.md` (project) or `~/.config/devin/skills/<name>/SKILL.md` (global) before improvising.
- When you learn a new domain deeply, distill it into a skill so the expertise persists across sessions.
- Prune skills that have been superseded or are no longer relevant.

### Skill quality standards (Devin CLI)

Every skill in this bundle must pass this checklist before commit:

1. **Frontmatter** — `name:` (lowercase, hyphens, max 64, matches directory) and `description:` (max 1024, under 500 if possible, starts with "Use when" and describes the trigger, not the workflow). Optional: `allowed-tools`, `permissions`, `subagent`, `agent`, `model`, `triggers`.
2. **Discovery-friendly** — description uses keywords an agent would search for; no workflow summary.
3. **Devin-native tools** — uses Devin CLI tool names: `exec`, `read`, `edit`, `write`, `grep`, `glob`, `run_subagent`, `web_search`, `mcp_call_tool`, `ask_user_question`. No Pascal-cased platform names, `Task(...)`, `subagent_type`, or non-Devin skill-invocation prefixes.
4. **Devin-native paths** — skills live in `.devin/skills/<name>/` or `~/.config/devin/skills/<name>/`. References use `.devin/`, `~/.config/devin/`, `%APPDATA%\devin\`. No non-Devin runtime paths.
5. **Subagents** — subagent dispatch uses `profile: "subagent_general"` or `profile: "subagent_explore"`; skill frontmatter may set `subagent: true` or `agent: <profile>`.
6. **Scripts** — helpers may be Python, Bash, or JavaScript as appropriate for the task and platform; prefer Python for cross-platform helpers.
7. **No AI signatures in skills** — skills do not commit on behalf of the user or inject signatures into deliverables.
8. **No platform leakage** — no references to non-Devin AI tools, platforms, runtimes, or their paths. Keep the skill Devin-CLI native.

## 4. Skill and tool discovery (first-time tasks each week)

- Before starting any non-trivial task, invoke `skill tool-and-skill-discovery` OR run `skill search` with relevant keywords and `skill list` on the project and global skill directories to find the best available skills.
- If a skill clearly matches the task, invoke it immediately at the start of the session (or before touching code).
- If more than one skill matches, invoke all relevant skills in parallel.
- If no matching skill exists, use `find-skills` to discover or propose one.
- Apply this rule to first occurrences of task categories each week: first PR, first PR review, first CSV edit, first project in a given language/stack, first deployment, first debugging session, first UI change, first installer/script work, first GitHub operation, first API/MCP integration, etc.
- This rule applies to all tools and integrations (MCP servers, skills, built-in commands, external CLIs, APIs, `gh`, `curl`, `python`, `powershell`) that can improve the task outcome.

## 5. Functional programming and clean code (always-on)

- **Default to functional programming:** prefer pure functions, immutability, and composition over mutation and imperative loops.
- **Functional Core, Imperative Shell (FCIS):** separate pure business logic (calculations) from side effects (actions). Gather inputs at the boundary, pass them to pure functions, then push results out.
- **Immutability first:** use `readonly`/`final`/`const` and change-by-copy methods where the language supports them.
- **Pipeline composition:** chain small functions (`map → filter → reduce`) instead of nested loops and temp variables.
- **Condense and reduce:** eliminate duplication via composition and higher-order functions. Fewer lines, fewer branches, fewer moving parts — without sacrificing clarity.
- **Readability is non-negotiable:** if a point-free pipeline or monad stack is harder to read than a simple loop, use the loop. Pragmatism over purity.
- **When not to apply:** one-off scripts, heavily stateful UIs managed by frameworks, hard-real-time systems where indirection adds latency.

## 6. Inner-loop validation (always-on)

- **Validate before you commit.** Run local checks (lint, typecheck, build, tests) before staging or committing code.
- **Mirror CI locally.** Whatever CI runs, run the same checks locally first. If no CI is configured, choose the smallest meaningful verification for the change.
- **Fix in the inner loop.** When a local check fails, fix it immediately — don't commit broken code hoping CI will catch it.
- **Scope checks to the change.** Run targeted tests when possible; run the full suite before push/PR.
- **No push without green.** Never push code that has known failing local checks. If a check is flaky, investigate it.
- **When CI fails, use `debug-ci-failures` skill.** Don't eyeball the logs — follow the systematic diagnosis workflow.

## 7. graphify trigger

- When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
