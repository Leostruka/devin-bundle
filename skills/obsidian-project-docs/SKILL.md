---
name: obsidian-project-docs
description: Use when the user wants to build or update a local codebase wiki in Obsidian with architecture diagrams, source-linked documentation, hierarchical pages, and auto-refresh.
---
# obsidian-project-docs

Build a **meticulous, SRS/ISO-style local codebase wiki** in an Obsidian vault at the same quality level as a cloud-generated wiki: source-linked documentation, hierarchical pages, architecture diagrams (Mermaid), codebase summaries, and a re-index workflow that keeps everything in sync with the code.

**Scope:** codebase summary, architecture, modules, functions, database schema, dependencies, config files, environment variables, relationships, decisions, diagrams, glossary, daily logbook, re-index.

## When to use

- "Document this codebase / project"
- "Build a local wiki for this repo"
- "Create architecture diagrams with source links"
- "Map all modules, functions, and dependencies with code references"
- "Visualize the system with Mermaid diagrams"
- Updating an existing engineering wiki after code changes

## Non-negotiable requirements

Every artifact produced by this skill MUST meet these standards:

1. **Source links** — every claim about code (module, function, class, route, schema, config) MUST cite the source file and line: `source: src/auth/login.ts:42`. No unsourced assertions. **Minimum 5 distinct source files cited per page.**
2. **Hierarchical pages** — every page has a `parent:` field in frontmatter (except the root). Pages form a tree, not a flat list.
3. **Diagrams** — Mermaid (inline, version-controllable). Minimum 13 types: Context, Container, Component, Domain, DataModel, Flow, Sequence, Class, State, C4Dynamic, C4Deployment, GitGraph, Mindmap.
4. **Codebase summary** — a top-level `00-Overview.md` that summarizes the entire system in 1-2 paragraphs with links to every other page.
5. **Re-index** — a `refresh.py` script in the vault that re-scans the codebase, detects changed files, and flags stale pages. Supports `--branch` for multi-branch awareness.
6. **Steering config** — a `wiki-config.json` in the vault that defines pages, priorities, notes, importance, filePaths, mode, and language (local equivalent of a cloud steering file). Validated by `validate_wiki_config.py`.
7. **Page structure** — every page starts with a `## Relevant source files` list and a `## Purpose and Scope` section, and ends each major section with a `Sources:` footer line.
8. **Code snippets** — pages about code embed real snippets from the source (not just links), fenced with the language tag.
9. **API depth** — function notes include Parameters table, Return value, Throws, and Examples (not just signature + side effects).
10. **Source column** — tables listing components, APIs, configs, or modules MUST include a `Source` column with `path:line` citations.
11. **Mermaid Sources blocks** — every Mermaid diagram includes a `<!-- Sources: path:line, path:line -->` comment block listing the files it visualizes.
12. **Local Q&A** — `query.py`, `wiki_structure.py`, `wiki_contents.py` scripts provide local equivalents of cloud wiki query tools.

## What is produced

Inside the target Obsidian vault:

| Artifact | File | Purpose |
|----------|------|---------|
| Overview | `00-Overview.md` | Codebase summary — 1-2 paragraphs, links to every page, entry point |
| SRS | `01-SRS.md` | Software Requirements Specification — scope, stakeholders, functional/non-functional requirements |
| Architecture | `02-Architecture.md` | System overview, layers, seams, adapters, data flow, ADRs, **source-linked** |
| Database | `03-Database.md` | Schema, tables, relationships, migrations, **source-linked** |
| Modules index | `04-Modules.md` + `Modules/*.md` | Module catalog with interfaces, invariants, tests, dependencies, **source-linked** |
| Functions index | `05-Functions.md` | Function registry, signatures, side effects, callers, **source-linked** |
| Dependencies | `06-Dependencies.md` | Third-party and internal dependencies with versions and rationale |
| Config | `07-Config.md` | Environment variables, config files, feature flags, **source-linked** |
| Glossary | `08-Glossary.md` | Domain terms with code references |
| Decisions | `09-Decisions.md` + `Decisions/*.md` | ADR log with context, decision, consequences |
| Project base | `Project.base` | Obsidian Base tying modules, functions, dependencies, config into a queryable database |
| Mermaid diagrams | `Diagrams/*.md` | Mermaid diagrams (Context, Container, Component, Domain, DataModel, Flow, Sequence, Class, State, C4Dynamic, C4Deployment, GitGraph, Mindmap) |
| Logbook | `Logbook.md` + `Daily/YYYY-MM-DD.md` | Running daily log of work, decisions, rationale |
| Steering config | `wiki-config.json` | Page definitions, priorities, notes, importance, filePaths, mode, language for steering wiki generation |
| Re-index script | `refresh.py` | Re-scans codebase, detects changes, flags stale pages, supports `--branch` |
| Config validator | `validate_wiki_config.py` | Validates `wiki-config.json` against the steering schema (page limits, note limits, unique titles) |
| Wiki structure | `wiki_structure.py` | Local equivalent of `read_wiki_structure` — dumps the page tree |
| Wiki contents | `wiki_contents.py` | Local equivalent of `read_wiki_contents` — dumps a page's full content |
| Wiki query | `query.py` | Local equivalent of `ask_question` — keyword search across the wiki returning pages + snippets + sources |
| Manifest | `project-manifest.json` | Project metadata, vault metadata, last-indexed timestamp, indexed branch |

## Quick start

```bash
# 1. Scaffold a new vault/project wiki
python <skill-dir>/scaffold.py --project-dir C:\path\to\project --vault-dir C:\path\to\ObsidianVault\MyProject

# 2. Or into a folder inside the current project (Git-tracked docs)
python <skill-dir>/scaffold.py --project-dir . --vault-dir ./docs/obsidian

# 3. After code changes, re-index to flag stale pages (optionally for a branch)
python <vault-dir>/refresh.py --project-dir C:\path\to\project [--branch main]

# 4. Validate the steering config
python <vault-dir>/validate_wiki_config.py

# 5. Query the wiki locally (equivalent of Ask Devin / read_wiki_*)
python <vault-dir>/wiki_structure.py                          # page tree
python <vault-dir>/wiki_contents.py --page "02-Architecture"  # full page content
python <vault-dir>/query.py --query "authentication flow"     # keyword search
```

Then invoke the rest of this skill to fill each artifact from code and conversation.

## Workflow

### Step 0 — Detect or confirm target

1. If the user gave a vault path, use it. Otherwise default to `<project>/docs/obsidian/`.
2. If the vault/docs folder already contains the artifact files, this is an **update** run. Read them first, then run `refresh.py` to identify stale pages.
3. If the files do not exist, run the scaffold script in Step 1.

### Step 1 — Scaffold the vault

```bash
python <skill-dir>/scaffold.py --project-dir <PROJECT> --vault-dir <VAULT>
```

The helper creates:
- The file tree (all pages with `parent:` frontmatter)
- Mermaid diagram shells (`Diagrams/*.md`) — 13 types
- `Project.base`
- `wiki-config.json` (steering config with `mode`, `language`, `importance`, `filePaths`)
- `refresh.py` (re-index script with `--branch` support)
- `validate_wiki_config.py` (steering config validator)
- `wiki_structure.py`, `wiki_contents.py`, `query.py` (local Q&A scripts)
- `project-manifest.json` (with `indexed_branch`)

### Step 2 — Fill `wiki-config.json` (steering)

Read the codebase structure first (`ls`, `tree`, `git ls-files`, or `graphify`). Then fill the steering config:

```json
{
  "mode": "comprehensive",
  "language": "en",
  "repo_notes": [
    {
      "content": "This repo has a frontend/ (React), backend/ (Node API), and infra/ (Terraform). Backend is highest priority.",
      "author": "agent"
    }
  ],
  "pages": [
    { "title": "Overview", "purpose": "Codebase summary and entry point", "parent": null, "importance": "high", "filePaths": ["README.md", "package.json"] },
    { "title": "Architecture", "purpose": "System layers, seams, data flow", "parent": "Overview", "importance": "high", "filePaths": ["src/"], "page_notes": [{"content": "Emphasize the auth seam.", "author": "agent"}] },
    { "title": "Auth Module", "purpose": "Authentication flow, OAuth2, session management", "parent": "Architecture", "importance": "high", "filePaths": ["src/auth/"] },
    { "title": "Database", "purpose": "Schema, tables, relationships", "parent": "Architecture", "importance": "medium", "filePaths": ["migrations/", "src/models/"] }
  ]
}
```

Fields:
- `mode` (optional): `"comprehensive"` (more pages, nested, high detail) or `"concise"` (fewer pages, flat, medium detail). Defaults to `comprehensive`.
- `language` (optional): ISO code (`en`, `pt`, `es`, `ja`, `zh`, `ko`, `vi`, `he`). The agent generates the wiki in this language. Defaults to `en`.
- `repo_notes`: array of `{content, author}`. Max 10,000 chars per note.
- `pages`: array of page definitions. If omitted, the agent auto-discovers structure via cluster-based planning (use `graphify` or `ls`/`tree` to identify modules and communities).
- Each page: `title` (unique, non-empty), `purpose`, `parent` (or `null` for root), `importance` (`high`/`medium`/`low`), `filePaths` (array of paths/files this page documents — used for retrieval), `page_notes` (array of `{content, author}`).

Validation limits (enforced by `validate_wiki_config.py`):
- Max 30 pages (80 for enterprise-scale vaults)
- Max 100 total notes (repo_notes + all page_notes combined)
- Max 10,000 characters per note
- Page titles must be unique and non-empty

### Step 3 — Build the Overview (`00-Overview.md`)

Read the codebase structure, README, package files, and any existing docs. The Overview page must include:

1. `## Relevant source files` — list the key files (README, package manifests, entry points) with source links.
2. `## Purpose and Scope` — 1-2 paragraph summary answering:
   - What does this system do?
   - What are the main components?
   - What technologies are used?
   - Where do I start reading the code?
3. `## Quick links` — wikilinks to every other page.
4. `## Diagrams` — wikilinks to every diagram.
5. `Sources:` footer citing the files used.

Link to every other page: `[[02-Architecture]], [[04-Modules]], [[03-Database]], ...`

This page is the **entry point** — anyone landing in the vault should understand the system from this page alone.

#### Cluster-based planning (when `pages` is omitted from `wiki-config.json`)

If the steering config has `repo_notes` but no `pages` array, auto-discover the page structure:

1. Run `graphify <project-dir> --no-viz` or use `ls`/`tree`/`git ls-files` to map the codebase.
2. Identify communities/clusters of related files (graphify does this; or group by top-level directory).
3. Create one page per cluster, with `parent` set to the most logical ancestor.
4. Assign `importance` based on cluster size and centrality (high for core modules, medium for supporting, low for peripheral).
5. Assign `filePaths` to each page from the cluster's files.
6. Cap at 30 pages (80 for enterprise); merge small clusters into a parent.

### Step 4 — SRS (`01-SRS.md`)

Read any existing README, specs, issues, or conversation context. The SRS page must include:

1. `## Relevant source files` — specs, README, issues, config files.
2. `## Purpose and Scope` — what the SRS covers.
3. Sections:
   - Purpose and scope
   - Stakeholders and actors
   - Functional requirements (numbered, testable, **traced to modules with source links**)
   - Non-functional requirements (performance, security, reliability)
   - Constraints and assumptions
   - Acceptance criteria
4. Each section ends with a `Sources:` footer.
5. Minimum 5 distinct source files cited.

Use callouts for risk or open questions:

```markdown
> [!warning] Open question
> The failover strategy is not yet defined.
```

### Step 5 — Architecture (`02-Architecture.md`)

Use the `codebase-design` vocabulary (module, interface, seam, adapter, depth, leverage, locality). The page must include:

1. `## Relevant source files` — key architectural files (entry points, config, module indices).
2. `## Purpose and Scope` — what this architecture page documents.
3. Sections, each ending with a `Sources:` footer:
   - Architectural drivers
   - Layers and modules — **each with `source: path/to/file.ext:line`**
   - Seams and adapters — **with source links**
   - Data flow
   - External integrations
   - ADRs (link to `Decisions/*.md`)
4. Embed code snippets for key seams/adapters (fenced, with language tag).
5. Minimum 5 distinct source files cited.

Every architectural claim must cite the source file and line where it is implemented.

### Step 6 — Database (`03-Database.md`)

For each database / persistence layer. The page must include:

1. `## Relevant source files` — migrations, models, schema files, ORM config.
2. `## Purpose and Scope` — what persistence layers are documented.
3. Sections, each ending with a `Sources:` footer:
   - Technology and version — `source: package.json:23` or `source: requirements.txt:5`
   - Schema overview
   - Tables / collections with purpose — `source: migrations/001_create_users.sql:1`
   - Columns / fields, types, constraints, indexes — `source: src/models/User.ts:12`
   - Relationships (ER-style or wikilinks)
   - Migrations strategy
   - Backup / replication notes
4. Embed schema snippets (fenced SQL or model code).
5. Minimum 5 distinct source files cited.

### Step 7 — Modules and Functions catalog

For each module:

1. Create or update `Modules/<ModuleName>.md` from `templates/module-template.md`.
2. The module note must include:
   - `## Relevant source files` — the module's key files with source links.
   - `## Purpose and Scope` — what the module does.
   - Interface (public functions, classes, exported symbols) — `source: src/auth/Auth.ts:15`
   - Invariants and ordering constraints
   - Error modes
   - Dependencies (internal and external)
   - Tests — `source: tests/auth.test.ts:1`
   - Embedded code snippets for the public interface (fenced, with language tag).
   - `Sources:` footer at the end of each section.
3. Set `parent: 04-Modules` in frontmatter.
4. Update the central `04-Modules.md` index with a table (including `Source` column) and wikilinks.

For functions:

1. Scan the codebase for exported / public functions.
2. In `05-Functions.md`, build a registry table with a `Source` column:
   - Function, Module, Signature, Source (`path:line`), Side effects, Calls, Tests
3. **MANDATORY: Create one .md file per function in `Functions/`** using `templates/function-template.md`. Every function listed in the `05-Functions.md` registry table MUST have a corresponding `Functions/<name>.md` file. No exceptions. The word "critical" does NOT mean "optional" — if a function is listed in the registry, it gets a file. Each function note must include:
   - `## Relevant source files` — where the function is defined and tested.
   - `## Purpose and Scope` — what the function does and why it exists.
   - `## Signature` — fenced code block with the full signature.
   - `## Parameters` — table with Name, Type, Required, Description.
   - `## Return value` — type and description of possible values.
   - `## Throws` — possible exceptions and when they occur.
   - `## Side effects` — writes, network calls, events.
   - `## Examples` — working code examples from actual source (fenced, with language tag).
   - `## Callers` — what calls this function (wikilinks).
   - `## Tests` — link to test files with source links.
   - `Sources:` footer at the end.
4. Minimum 5 distinct source files cited per function note (where the function is complex enough).
5. **Validation**: after creating function pages, verify that the `Functions/` directory is not empty. If `05-Functions.md` lists N functions, `Functions/` must contain at least N `.md` files. Run `validate_wiki_structure.py` to confirm.

### Step 8 — Dependencies (`06-Dependencies.md`)

Read package managers and config files (`package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, etc.). List:

- Production dependencies (name, version, purpose, license if known) — `source: package.json:12`
- Development dependencies
- Internal dependencies (cross-module imports)
- Optional / runtime dependencies
- Deprecated or risky dependencies

### Step 9 — Config (`07-Config.md`)

Collect config artifacts with source links:

- Environment variables — `source: .env.example:3` or `source: src/config/index.ts:8`
- Config files — `source: docker-compose.yml:1`
- Feature flags and defaults
- Secrets management strategy

### Step 10 — Glossary (`08-Glossary.md`)

Use `domain-modeling` discipline. Copy or extend `CONTEXT.md` terms. Add:

- Domain term
- Definition
- Synonyms / aliases
- Where it appears in code — `source: src/types/Order.ts:5`

### Step 11 — Decisions (`09-Decisions.md` + `Decisions/*.md`)

For each architectural decision, create an ADR note:

```markdown
---
title: "ADR-001: Use OAuth2 for authentication"
parent: 09-Decisions
tags: [decision, adr]
date: 2026-01-15
status: accepted
---

# ADR-001: Use OAuth2 for authentication

## Context
_Why this decision was needed._

## Decision
_What was decided._

## Consequences
_What follows from this decision._
```

### Step 12 — Build / update the Project Base (`Project.base`)

The `.base` file ties everything together. Populate it with rows for modules, functions, dependencies, and config. Each row is an Obsidian note linked by `file.path`.

See `references/obsidian-bases-spec.md` for Base syntax.

### Step 13 — Build / update diagrams

Create Mermaid versions of each diagram. Use **modern diagrams** instead of (or alongside) heavy UML. See `references/modern-diagrams.md` for conventions.

#### Mermaid diagrams (`Diagrams/*.md`)

Mermaid renders inline in Obsidian and is version-controllable. Minimum 13 types:

- `Diagrams/Context.md` — C4 System Context
- `Diagrams/Container.md` — C4 Container
- `Diagrams/Component.md` — C4 Component for the most critical container
- `Diagrams/Domain.md` — DDD context map
- `Diagrams/DataModel.md` — ER/data model
- `Diagrams/Flow.md` — Event / data flow
- `Diagrams/Sequence.md` — Sequence diagram for critical interactions (e.g., auth flow, checkout)
- `Diagrams/Class.md` — Class diagram for core domain types and inheritance
- `Diagrams/State.md` — State machine for entities with lifecycle (e.g., order status)
- `Diagrams/C4Dynamic.md` — C4 Dynamic diagram for runtime collaborations
- `Diagrams/C4Deployment.md` — C4 Deployment diagram for infrastructure topology
- `Diagrams/GitGraph.md` — Git branching/merge strategy
- `Diagrams/Mindmap.md` — Mindmap for feature/domain brainstorming

Every Mermaid diagram MUST include a `<!-- Sources: ... -->` comment block listing the source files it visualizes:

```markdown
---
parent: 02-Architecture
tags: [diagram, c4, context]
---

# System Context

<!-- Sources: src/index.ts:1, src/config.ts:12, package.json:5 -->

\`\`\`mermaid
graph TB
  User([User]) --> System[MyApp]
  System --> Email[Email Service]
  System --> Payment[Payment Gateway]
\`\`\`

## Links
- [[02-Architecture]]
- [[Modules/Auth]]
```

Each diagram should:

- Use node colors consistently (green internal, yellow DB, orange queue, red external, purple actor)
- Label every edge with the relationship and technology
- Include a small legend
- Link back to the relevant note

You may use `graphify` first to extract the code graph and then translate key nodes and edges into the diagrams.

### Step 14 — Re-index workflow (`refresh.py`)

The scaffold writes a `refresh.py` script into the vault. After code changes, run:

```bash
python <vault-dir>/refresh.py --project-dir <PROJECT> [--branch <BRANCH>]
```

It will:

1. Scan the project directory for files changed since `project-manifest.json` `last_indexed`.
2. For each changed file, find which wiki pages reference it (grep for `source: <file>`).
3. Print a report: which pages are stale and need updating.
4. If `--branch` is provided, record the indexed branch in `project-manifest.json` and compare against the previously indexed branch (warn if different).
5. Update `last_indexed` and `indexed_branch` in `project-manifest.json`.

This is the local equivalent of auto-reindexing. Run it before any update pass to know exactly which pages need attention.

#### Auto-refresh trigger (optional)

For automatic re-indexing, set up a git post-commit hook in the project:

```bash
# .git/hooks/post-commit
python /path/to/vault/refresh.py --project-dir . --branch "$(git rev-parse --abbrev-ref HEAD)" >> /path/to/vault/.refresh.log 2>&1
```

Or use a scheduled task / cron to run `refresh.py` periodically (e.g., every 2 hours, matching cloud cadence).

### Step 15 — Maintain the Logbook (`Logbook.md` and `Daily/YYYY-MM-DD.md`)

At the end of each session create or update the daily note:

1. Open `Daily/YYYY-MM-DD.md` from `templates/daily-note-template.md`.
2. Fill:
   - **Context** — current focus
   - **Done** — what was completed
   - **Tried** — experiments or approaches
   - **What worked** — with rationale and evidence
   - **What failed / blocked** — with lessons
   - **Decisions made** — decision, rationale, consequences, linked ADR
   - **Open questions**
   - **Next** — next actions
3. Append a link to `Logbook.md` under the `## Activity log` heading, grouped by week or month.

Use tags: `#decision`, `#blocker`, `#try`, `#success`, `#revert`, `#investigate`.

## Running with graphify

If the project has many files, run `/graphify <project-dir> --no-viz` before documenting. Use the resulting `graphify-out/graph.json` and `GRAPH_REPORT.md` to identify:

- Modules and communities
- Dependency edges
- Central vs peripheral nodes
- Unresolved or ambiguous relationships

Then write the findings into the Obsidian vault using this skill.

## Deviation / exceptions

- If the project is not a software project, fall back to `grill-with-docs` or `domain-modeling`.
- If the user only wants diagrams, use `references/modern-diagrams.md` and skip the SRS.
- If the user only wants a database schema, use `03-Database.md` and the `Modules/Database/` notes.

## Quality checklist

- [ ] `00-Overview.md` exists and summarizes the system in 1-2 paragraphs with links to all pages.
- [ ] Every page has a `parent:` field in frontmatter (except `00-Overview.md`).
- [ ] Every page starts with `## Relevant source files` and `## Purpose and Scope`.
- [ ] Every major section ends with a `Sources:` footer line.
- [ ] Every claim about code has a `source: path/to/file.ext:line` citation.
- [ ] Every page cites at least 5 distinct source files.
- [ ] Tables listing components, APIs, configs, or modules include a `Source` column.
- [ ] Every Mermaid diagram includes a `<!-- Sources: ... -->` comment block.
- [ ] Pages about code embed real code snippets (fenced, with language tag).
- [ ] Function notes include Parameters, Return value, Throws, and Examples.
- [ ] **Every function listed in `05-Functions.md` has a corresponding `Functions/<name>.md` file** (not just a table row). `Functions/` directory must not be empty.
- [ ] Every module has a `Modules/*.md` note with interface, dependencies, and source links.
- [ ] Every functional requirement in `01-SRS.md` is traceable to a module or function with a source link.
- [ ] `06-Dependencies.md` matches the package manager files (with source links).
- [ ] `07-Config.md` includes all env vars and config files (with source links).
- [ ] `Project.base` renders as a table in Obsidian.
- [ ] All 13 Mermaid diagram types exist (`Diagrams/*.md`).
- [ ] `wiki-config.json` exists with page definitions, repo notes, mode, language, importance, filePaths.
- [ ] `validate_wiki_config.py` exists and passes without errors.
- [ ] `refresh.py` exists, runs without errors, and supports `--branch`.
- [ ] `wiki_structure.py`, `wiki_contents.py`, `query.py` exist and run without errors.
- [ ] `project-manifest.json` records `indexed_branch`.
- [ ] `Logbook.md` links to every `Daily/YYYY-MM-DD.md` entry.
- [ ] Daily notes capture context, done, tried, worked, failed, decisions, rationale and next actions.
- [ ] All internal references use Obsidian wikilinks `[[...]]`.
- [ ] Wiki content is in the `language` specified in `wiki-config.json`.

## Templates and references

- `templates/srs-template.md`
- `templates/module-template.md`
- `templates/database-template.md`
- `templates/config-template.md`
- `templates/function-template.md`
- `templates/daily-note-template.md`
- `templates/overview-template.md`
- `templates/adr-template.md`
- `references/obsidian-bases-spec.md`
- `references/modern-diagrams.md`
