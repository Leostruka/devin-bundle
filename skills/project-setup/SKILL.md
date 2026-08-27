---
name: project-setup
description: Use when starting work on a new or existing project that lacks a `.devin/` configuration, or when the user wants to add skills, hooks, rules, and local tools to a project in a systematic, validated way.
version: 1.0.0
---

# Project Setup

Set up a Devin CLI project workspace inside `.devin/` only. This is a systematic, validated workflow that adapts the `continuous-improvement` 10-step loop to project onboarding.

## Principle

Every project that the agent touches deserves a predictable, auditable `.devin/` setup. Nothing agent-facing is written outside `.devin/`. The skill does not write business code or install project dependencies unless they are required for the agent to function.

## When to use

- The repo has no `.devin/` directory.
- `.devin/` exists but is incomplete (no rules, no hooks, no skills, no memory, no agent config).
- The user asks to "set up the project for the agent", "add skills/hooks", or "prepare this repo for Devin CLI".

## When NOT to use

- The project already has a complete `.devin/` and the user wants a specific edit — use `/self-extend` instead.
- The task is to write application code — use `/implement` or `/tdd`.
- The user only wants a global config change — use `~/.config/devin/` paths.

## FASE 0 — Deep Research (before any change)

Run these checks in order and record the evidence. Do not proceed until each step has a concrete output.

1. **Inspect the repo.**
   - `git remote -v` and `.git/config` — GitHub, GitLab, or none?
   - `ls -la` (or `Get-ChildItem`) at the repo root — what files and directories already exist?
   - Look for `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `pnpm-workspace.yaml`, `go.mod`, `pom.xml`, or similar stack signals.
   - Look for `src/`, `packages/*`, `apps/*`, `tests/` to detect monorepo.

2. **Inspect existing `.devin/` (if any).**
   - `ls -la .devin/` — what is already configured?
   - Read `.devin/config.json`, `.devin/hooks.v1.json`, `.devin/mcp_config.json` if they exist.
   - List `.devin/skills/*/` and `.devin/rules/*.md`.

3. **Confirm Devin CLI conventions.**
   - Rules: `.devin/global_rules.md` and `.devin/rules/*.md` (sources: Devin CLI docs, `self-extend` skill).
   - Skills: `.devin/skills/<name>/SKILL.md`.
   - Hooks: `.devin/hooks.v1.json`.
   - MCP: `.devin/mcp_config.json` and `.devin/mcp_config.local.json` (gitignored).
   - Memory: `.devin/memory/` (see `/project-memory`).

4. **List the bundle resources available.**
   - Read the global bundle `config.json`, `manifest.json`, and `AGENTS.md` to know which skills, scripts, and hooks can be copied into the project.

## LOOP DE SETUP (10 passos)

### Passo 1 — OBSERVAR

Record the current state in a ledger at `.devin/ledgers/project-setup.md` (create the `ledgers/` directory if it does not exist):

```markdown
# Project setup: <repo-name>

## Observed
- Stack: <detected stack>
- Monorepo: <yes/no>
- Remote: <github/gitlab/none>
- Existing `.devin/`: <list files>

## Missing
- <rule file>
- <hook file>
- <skill file>
- <memory dir>
```

### Passo 2 — CRITICAR

Compare the observed state against the rule: **all agent files must live in `.devin/`**. Identify every missing or mis-placed item. For each missing item, note which bundle resource should provide it.

### Passo 3 — GERAR ALTERNATIVAS

For each missing component, generate at least two alternatives and record trade-offs:

| Component | Alt 1 | Alt 2 | Alt 3 | Best fit |
|---|---|---|---|---|
| Issue tracker | GitHub (gh) | Local markdown | GitLab | depends on `git remote` |
| Rules | `.devin/global_rules.md` | `.devin/rules/*.md` | both | both |
| Memory | `.devin/memory/` | none | — | always enable |
| Hooks | copy bundle hooks | create minimal set | none | copy from bundle |
| MCP | `.devin/mcp_config.json` template | none | — | ask user |

### Passo 4 — REVISAR

Apply the best-fit alternative for each component. This is the deterministic setup order:

1. **Run `setup-matt-pocock-skills`** to configure issue tracker, triage labels, and domain docs (all inside `.devin/`).
2. **Create `.devin/global_rules.md`** with a short `## Agent skills` block and the repo-specific rules from `setup-matt-pocock-skills`.
3. **Create `.devin/rules/*.md`** for optional, trigger-scoped rules.
4. **Create `.devin/hooks.v1.json`** with the essential hooks from the bundle:
   - `behavioral-nudge.py` on `UserPromptSubmit`
   - `check-ai-signature.py` on `PreToolUse` for `write`/`edit`
   - `check-push-green.py` on `PreToolUse` for `exec`
   - `destructive-gate.py` on `PreToolUse` for `exec`
   - `context-budget.py` on `SessionStart`
   - `memory-retrieval.py` on `UserPromptSubmit`
   - `memory-post-edit.py` on `PostToolUse` for `write`/`edit`
   - `memory-post-exec.py` on `PostToolUse` for `exec`
   - `memory-stop.py` on `Stop`
5. **Create `.devin/mcp_config.json`** as an empty scaffold if the project has no MCP servers; otherwise ask the user which servers to add.
6. **Create `.devin/skills/project-memory/`** if it does not exist, copying `note.md`, `capture-memory.py`, `query-memory.py`, and `audit-memory.py` from the bundle. Use `/project-memory` to walk the user through the first capture.
7. **Create `.devin/skills/setup-matt-pocock-skills/`** link or copy if the user wants the engineering flow available locally.
8. **Create `.devin/memory/`** directory and seed `MOC.md`.

### Passo 5 — VALIDAR

Run the project-level validation suite:

- `python audit.py` in the project root if the project has one.
- If no project audit exists, run a minimal structural check:
  - `ls .devin/global_rules.md`, `.devin/hooks.v1.json`, `.devin/mcp_config.json`, `.devin/skills/`, `.devin/memory/`
  - `python -m json.tool .devin/hooks.v1.json`
  - `python -m json.tool .devin/mcp_config.json`

### Passo 6 — FUTURE PACE

Project the setup against 3 hypothetical future sessions:

1. **New feature request** — does the agent know where to write tickets, capture memory, and read domain docs?
2. **Code review request** — does the agent find the standards sources and the `AGENTS.md` rule block?
3. **Multi-session task** — does the agent have memory retrieval hooks and a local issue tracker to record progress?

At least two must be clearly helped; otherwise the setup is incomplete.

### Passo 7 — ECOLOGICAL CHECK

Check for side effects:

- Did the setup create any file outside `.devin/`? If yes, delete or move it.
- Did any hook conflict with an existing project hook?
- Is the `context-budget.py` hook adding too much token cost?
- Are there duplicate skills in `.devin/skills/` and `%APPDATA%/devin/skills/`?

### Passo 8 — SIMULAR

Run `install.ps1 -Force` (or copy the `.devin/` files) and restart a fresh Devin CLI session against the project. Verify:

- `skill list --path .devin/skills` shows the local skills.
- `python audit.py` (or the structural check) passes.
- A test `write` to a project file triggers `check-ai-signature.py` (if configured).

### Passo 9 — CLASSIFICAR

Classify the setup:

| Classe | Critério | Ação |
|---|---|---|
| **MELHOROU** | All 3 future scenarios helped, no side effects, validation passed | Mark ledger as `done` |
| **NEUTRO** | Validation passed, no side effects, but <2 scenarios helped | Revisit missing component |
| **PIOROU** | Validation failed or side effects found | Revert the offending change and return to Passo 3 |
| **INCONCLUSIVO** | Could not simulate (no fresh session) | Do not declare done; ask user to test |

### Passo 10 — REPETIR OU CONVERGIR

- If the user asks for more tools, skills, or hooks, return to **Passo 1** and update the ledger.
- If nothing more is requested and the setup is classified **MELHOROU** or **NEUTRO**, the setup is complete.

## Output format

When finishing, report:

```
SETUP: <repo-name>
OBSERVED: <stack> | <monorepo> | <remote>
FASE0: <sources checked>
COMPONENTS: <list of .devin/ files created or updated>
VALIDATION: <pass|fail>
FUTURE_PACE: <n/3 scenarios helped>
ECOLOGICAL: <side effects or none>
CLASSIFICATION: <MELHOROU|NEUTRO|PIOROU|INCONCLUSIVO>
PENDING: <what the user still needs to decide or provide>
```

## Red flags — STOP and ask

- The user asks to write files outside `.devin/`.
- A requested hook conflicts with the project's CI or security policy.
- The user wants to skip `setup-matt-pocock-skills` but still use `triage`, `planning-pipeline`, or `wayfinder`.
- A proposed MCP server requires a secret that the user has not provided.

## Common mistakes

- Copying every global skill into the project. Only copy skills that benefit from project-specific tuning; the global bundle is still available.
- Creating `AGENTS.md` at the project root. Always prefer `.devin/global_rules.md`.
- Skipping the ledger. Without a ledger, the agent cannot prove completion.
- Skipping simulation. A setup that is not loaded by a fresh session is not done.

## Cross-references

- `/setup-matt-pocock-skills` — issue tracker, triage labels, domain docs.
- `/project-memory` — capture and retrieve project knowledge.
- `/self-extend` — add individual rules, skills, hooks, or MCP servers.
- `/continuous-improvement` — the 10-step loop this skill adapts.
