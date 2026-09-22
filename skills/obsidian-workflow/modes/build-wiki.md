# Mode: Build Wiki

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
3. **Diagrams** — Mermaid (inline, version-controllable). 14 types (numbered `{NN}-{Name}.md`): 01-Context, 02-Container, 03-Component, 04-Domain, 05-DataModel, 06-Flow, 07-Sequence, 08-Class, 09-State, 10-C4Dynamic, 11-C4Deployment, 12-GitGraph, 13-Mindmap, 14-Architecture.
4. **Codebase summary** — a top-level `00-Overview.md` that summarizes the entire system in 1-2 paragraphs with links to every other page.
5. **Re-index** — a `refresh.py` script in the vault that re-scans the codebase, detects changed files, and flags stale pages. Supports `--branch` for multi-branch awareness.
6. **Steering config** — a `wiki-config.json` in the vault that defines pages, priorities, notes, importance, filePaths, mode, and language (local equivalent of a cloud steering file). Validated by `validate_wiki_config.py`.
7. **Page structure** — every page starts with a `## Relevant source files` list and a `## Purpose and Scope` section, and ends each major section with a `Sources:` footer line.
8. **Code snippets** — pages about code embed real snippets from the source (not just links), fenced with the language tag.
9. **API depth** — function notes include Parameters table, Return value, Throws, and Examples (not just signature + side effects).
10. **Source column** — tables listing components, APIs, configs, or modules MUST include a `Source` column with `path:line` citations.
11. **Mermaid Sources blocks** — every Mermaid diagram includes a `<!-- Sources: path:line, path:line -->` comment block listing the files it visualizes. **Must be OUTSIDE the ` ```mermaid ` block** (before it), never inside — HTML comments inside Mermaid break rendering.
12. **Mermaid syntax** — all diagrams must use valid Mermaid syntax. Common errors to avoid:
    - `<!-- Sources: -->` inside ` ```mermaid ` block (breaks rendering — move outside)
    - Unclosed generics: `Items~` (odd `~` count) — use `Items[]` or `List~Items~`
    - `<br///` (triple slash) — use `<br/>`
    - `NODE fill:...` without `style` keyword — use `style NODE fill:...`
    - ``mermaid (single/double backtick) — use triple ` ```mermaid `
    - `subgraph` without matching `end`
13. **Local Q&A** — `query.py`, `wiki_structure.py`, `wiki_contents.py` scripts provide local equivalents of cloud wiki query tools.

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
| Logbook | `10-Logbook.md` + `Daily/YYYY-MM-DD.md` | Running daily log of work, decisions, rationale |
| Steering config | `wiki-config.json` | Page definitions, priorities, notes, importance, filePaths, mode, language for steering wiki generation |
| Re-index script | `refresh.py` | Re-scans codebase, detects changes, flags stale pages, supports `--branch` |
| Config validator | `validate_wiki_config.py` | Validates `wiki-config.json` against the steering schema (page limits, note limits, unique titles) |
| Wiki structure | `wiki_structure.py` | Local equivalent of `read_wiki_structure` — dumps the page tree |
| Wiki contents | `wiki_contents.py` | Local equivalent of `read_wiki_contents` — dumps a page's full content |
| Wiki query | `query.py` | Local equivalent of `ask_question` — keyword search across the wiki returning pages + snippets + sources |
| Manifest | `project-manifest.json` | Project metadata, vault metadata, last-indexed timestamp, indexed branch |
| Tech Debt | `11-TechDebt.md` | Anti-patterns, optimization opportunities, dependency risks, missing tests (effort: medium/high only) |

## Quick start

```bash
# 1. Scaffold a new vault/project wiki
python <skill-dir>/scripts/scaffold.py --project-dir C:\path\to\project --vault-dir C:\path\to\ObsidianVault\MyProject

# 2. Or into a folder inside the current project (Git-tracked under .devin/)
python <skill-dir>/scripts/scaffold.py --project-dir . --vault-dir ./.devin/obsidian

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

#### Step 0 — Detect or confirm target

1. If the user gave a vault path, use it. Otherwise default to `<project>/.devin/obsidian/`. If that does not exist and `<project>/docs/obsidian/` already exists, use the legacy path instead.
2. If the vault folder already contains the artifact files, this is an **update** run. Read them first, then run `refresh.py` to identify stale pages.
3. If the files do not exist, run the scaffold script in Step 1.

#### Step 0.5 — Confirm information sources

Before scaffolding or filling any page, **ask the user** whether the agent has means to acquire the necessary information to document the project. Use `ask_user_question` with the following:

> **Question:** "I have access to the project directory at `<path>`. Can I acquire all the information I need from the codebase and files there, or do you need to provide additional context?"
>
> **Options:**
> 1. **"Codebase is sufficient"** — the agent can read all source files, configs, READMEs, migrations, and tests. No external context needed. Proceed to Step 1.
> 2. **"I'll provide additional context"** — the user has information not in the codebase (business rules, stakeholder needs, infrastructure details, API contracts, historical decisions). The agent asks follow-up questions (see below).
> 3. **"Partial — I'll supplement"** — the agent reads what it can from the codebase, then asks the user to fill gaps discovered during exploration.

**If the user chooses option 2 or 3**, ask for the missing information using `ask_user_question` (one question per call, max 4 questions per call). Cover these categories as needed:

| Category | What to ask |
|----------|-------------|
| **Business context** | What does the system do from the customer's perspective? Who are the stakeholders and actors? |
| **Architecture** | Are there external services, integrations, or infrastructure not visible in the code? (DNS, SSL, CI/CD, hosting, DB connections) |
| **Database** | Is there a schema or ER diagram available? Are there external databases not in the repo? |
| **API contracts** | Are there external API specs (OpenAPI, Postman, docs) not in the repo? |
| **Decisions** | Are there architectural decisions (ADRs) the user wants documented that aren't in the code or git history? |
| **Constraints** | Regulatory, business, or technical constraints not visible in the code? |
| **Glossary** | Domain terms, acronyms, or business vocabulary the user wants defined? |
| **Environment** | Production/staging URLs, server specs, deployment process not in the repo? |

**Rules:**
- Do NOT proceed to Step 1 until the user has confirmed the information sources (option 1) or has answered the follow-up questions (options 2/3).
- If the user selects option 3 ("Partial"), proceed to Step 1, read the codebase, then come back and ask about gaps discovered during exploration.
- Save user-provided context in `wiki-config.json` under `repo_notes` (with `author: "user"`) so it persists for future re-index runs.
- Never guess or fabricate information the user didn't provide. If a page cannot be filled from code or user input, leave it as a stub with a `> [!warning] Needs user input` callout.

#### Step 1 — Scaffold the vault

```bash
python <skill-dir>/scripts/scaffold.py --project-dir <PROJECT> --vault-dir <VAULT>
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

#### Step 2 — Fill `wiki-config.json` (steering)

Read the codebase structure first (`ls`, `tree`, or `git ls-files`). Then fill the steering config:

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
- `pages`: array of page definitions. If omitted, the agent auto-discovers structure via cluster-based planning (use `ls`/`tree` to identify modules and communities).
- Each page: `title` (unique, non-empty), `purpose`, `parent` (or `null` for root), `importance` (`high`/`medium`/`low`), `filePaths` (array of paths/files this page documents — used for retrieval), `page_notes` (array of `{content, author}`).

Validation limits (enforced by `validate_wiki_config.py`):
- Max 30 pages (80 for enterprise-scale vaults)
- Max 100 total notes (repo_notes + all page_notes combined)
- Max 10,000 characters per note
- Page titles must be unique and non-empty

#### Step 3 — Build the Overview (`00-Overview.md`)

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

##### Cluster-based planning (when `pages` is omitted from `wiki-config.json`)

If the steering config has `repo_notes` but no `pages` array, auto-discover the page structure:

1. Use `ls`/`tree`/`git ls-files` to map the codebase.
2. Identify communities/clusters of related files (group by top-level directory).
3. Create one page per cluster, with `parent` set to the most logical ancestor.
4. Assign `importance` based on cluster size and centrality (high for core modules, medium for supporting, low for peripheral).
5. Assign `filePaths` to each page from the cluster's files.
6. Cap at 30 pages (80 for enterprise); merge small clusters into a parent.

#### Step 4 — SRS (`01-SRS.md`)

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

#### Step 5 — Architecture (`02-Architecture.md`)

Use the `architecture` vocabulary (module, interface, seam, adapter, depth, leverage, locality). The page must include:

1. `## Relevant source files` — key architectural files (entry points, config, module indices).
2. `## Purpose and Scope` — what this architecture page documents.
3. Sections, each ending with a `Sources:` footer:
   - Architectural drivers
   - Layers and modules — **each with `source: path/to/file.ext:line`**
   - Seams and adapters — **with source links**
   - Data flow
   - External integrations
   - ADRs (link to `Decisions/*.md`)
4. **`## Diagrams` section** — wikilinks to ALL 14 `Diagrams/*.md` files. This is MANDATORY — without it, diagram pages become graph orphans (no inbound links). Format:
   ```markdown
   ## Diagrams
   - [[Diagrams/01-Context|Context]] · [[Diagrams/02-Container|Container]] · [[Diagrams/03-Component|Component]] · [[Diagrams/04-Domain|Domain]]
   - [[Diagrams/05-DataModel|Data Model]] · [[Diagrams/06-Flow|Flow]] · [[Diagrams/07-Sequence|Sequence]] · [[Diagrams/08-Class|Class]]
   - [[Diagrams/09-State|State]] · [[Diagrams/10-C4Dynamic|C4 Dynamic]] · [[Diagrams/11-C4Deployment|C4 Deployment]] · [[Diagrams/12-GitGraph|Git Graph]]
   - [[Diagrams/13-Mindmap|Mindmap]] · [[Diagrams/14-Architecture|Architecture Overview]]
   ```
5. Embed code snippets for key seams/adapters (fenced, with language tag).
6. Minimum 5 distinct source files cited.

Every architectural claim must cite the source file and line where it is implemented.

#### Step 6 — Database (`03-Database.md`)

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

#### Step 7 — Modules and Functions catalog

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
   - **MANDATORY: The Function column MUST be a wikilink** — `[[Functions/<name>|<name>]]` — not plain text. Without this, function pages become graph orphans (no inbound links). Example:
     ```markdown
     | Function | Module | Signature | Source | Side Effects | Callers |
     |----------|--------|-----------|--------|--------------|---------|
     | [[Functions/notify\|notify]] | Mlt2mController | `notify(): void` | `source: controllers/Mlt2mController.php:124` | HTTP response, DB write | Router |
     | [[Functions/getOrder\|getOrder]] | OrderService | `getOrder($id, $user): Order\|false` | `source: services/OrderService.php:62` | ML API call | processOrder() |
     ```
   - In markdown tables, escape the pipe in the alias: `[[Functions/notify\|notify]]`
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
5. **Validation**: after creating function pages, verify that the `Functions/` directory is not empty. If `05-Functions.md` lists N functions, `Functions/` must contain at least N `.md` files. Run `scripts/validate_wiki_structure.py` to confirm.

#### Step 8 — Dependencies (`06-Dependencies.md`)

Read package managers and config files (`package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, etc.). List:

- Production dependencies (name, version, purpose, license if known) — `source: package.json:12`
- Development dependencies
- Internal dependencies (cross-module imports)
- Optional / runtime dependencies
- Deprecated or risky dependencies

#### Step 9 — Config (`07-Config.md`)

Collect config artifacts with source links:

- Environment variables — `source: .env.example:3` or `source: src/config/index.ts:8`
- Config files — `source: docker-compose.yml:1`
- Feature flags and defaults
- Secrets management strategy

#### Step 10 — Glossary (`08-Glossary.md`)

Use `knowledge-modeling` discipline. Copy or extend `.devin/CONTEXT.md` terms. Add:

- Domain term
- Definition
- Synonyms / aliases
- Where it appears in code — `source: src/types/Order.ts:5`

#### Step 11 — Decisions (`09-Decisions.md` + `Decisions/*.md`)

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

#### Step 12 — Build / update the Project Base (`Project.base`)

The `.base` file ties everything together. Populate it with rows for modules, functions, dependencies, and config. Each row is an Obsidian note linked by `file.path`.

See `references/obsidian-bases-spec.md` for Base syntax.

#### Step 13 — Build / update diagrams

Create Mermaid versions of each diagram. Use **modern diagrams** instead of (or alongside) heavy UML. See `references/modern-diagrams.md` for conventions.

##### Mermaid diagrams (`Diagrams/*.md`)

Mermaid renders inline in Obsidian and is version-controllable. 14 types (numbered `{NN}-{Name}.md`):

- `Diagrams/01-Context.md` — C4 System Context
- `Diagrams/02-Container.md` — C4 Container
- `Diagrams/03-Component.md` — C4 Component for the most critical container
- `Diagrams/04-Domain.md` — DDD context map
- `Diagrams/05-DataModel.md` — ER/data model
- `Diagrams/06-Flow.md` — Event / data flow
- `Diagrams/07-Sequence.md` — Sequence diagram for critical interactions (e.g., auth flow, checkout)
- `Diagrams/08-Class.md` — Class diagram for core domain types and inheritance
- `Diagrams/09-State.md` — State machine for entities with lifecycle (e.g., order status)
- `Diagrams/10-C4Dynamic.md` — C4 Dynamic diagram for runtime collaborations
- `Diagrams/11-C4Deployment.md` — C4 Deployment diagram for infrastructure topology
- `Diagrams/12-GitGraph.md` — Git branching/merge strategy
- `Diagrams/13-Mindmap.md` — Mindmap for feature/domain brainstorming
- `Diagrams/14-Architecture.md` — Architecture overview (consolidated: DNS, SSL, server, DB, CI/CD)

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

#### Step 14 — Re-index workflow (`refresh.py`)

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

##### Auto-refresh trigger (optional)

For automatic re-indexing, set up a git post-commit hook in the project:

```bash
# .git/hooks/post-commit
python /path/to/vault/refresh.py --project-dir . --branch "$(git rev-parse --abbrev-ref HEAD)" >> /path/to/vault/.refresh.log 2>&1
```

Or use a scheduled task / cron to run `refresh.py` periodically (e.g., every 2 hours, matching cloud cadence).

#### Step 15 — Maintain the Logbook (`10-Logbook.md` and `Daily/YYYY-MM-DD.md`)

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
3. Append a link to `10-Logbook.md` under the `## Activity log` heading, grouped by week or month.

Use tags: `#decision`, `#blocker`, `#try`, `#success`, `#revert`, `#investigate`.

**Daily note frontmatter standard (enforced by `scripts/validate_wiki_structure.py`):**

```yaml
---
title: "Project Name - YYYY-MM-DD"   # hyphen, not em-dash; quoted
date: "YYYY-MM-DD"                    # quoted, matches filename
project: "Project Name"               # quoted, matches 10-Logbook project field
parent: 10-Logbook                    # filename reference, unquoted
tags:                                 # YAML list, NOT inline [a, b]
  - logbook
  - project-tag
status: active                        # or inactive, matches project status
---
```

**10-Logbook.md frontmatter standard:**

```yaml
---
title: "Project Name - Logbook"       # hyphen, not em-dash; quoted
project: "Project Name"               # quoted
parent: 00-Overview                   # filename reference
tags:                                 # YAML list
  - logbook
  - project-tag
status: active                        # or inactive
---
```

#### Step 16 — Create project page and MOC

After all wiki pages are built, create the project's entry-point documents outside the `_wiki/` directory. These are the files users see first when browsing the vault.

**1. Project page (`ProjectName.md`)**

Create or update `<project-folder>/ProjectName.md` (sibling of `_wiki/`). This is the project's primary note with quick facts and wiki links.

```markdown
---
company: <Company>
type: web
subtype: <webapp|webpage|api|...>
usage: external
category: <institutional|commercialized|internal|...>
status: active
stack: [<Framework>, <Language>, <Database>, ...]
domain: <domain.com.br>
hosting: <Hosting provider>
server: <server hostname>
path: <server path>
repo: <org/repo>
updated: YYYY-MM-DD
---

# ProjectName

<1-2 paragraph summary of what the project is and does.>

## Quick Facts

| Item | Value |
|------|-------|
| **Public URL** | https://... |
| **GitHub** | org/repo (private/public) |
| **Hosting** | ... |
| **Server path** | ... |
| **Tech stack** | ... |
| **Database** | ... |
| **CDN/Proxy** | ... |
| **Deploy** | ... |

## Core Features

1. **Feature** (public/admin) — route description
2. ...

## Wiki

- [[00-Overview|Overview]] — ...
- [[01-SRS|SRS]] — ...
- [[02-Architecture|Architecture]] — ...
- [[03-Database|Database]] — ...
- [[04-Modules|Modules]] — ...
- [[05-Functions|Functions]] — ...
- [[06-Dependencies|Dependencies]] — ...
- [[07-Config|Config]] — ...
- [[08-Glossary|Glossary]] — ...
- [[09-Decisions|Decisions]] — ...
- [[10-Logbook|Logbook]] — ...

## Subdomain of / Parent

- [[ParentProject]]

## Related

- [[RelatedProject1]]
- [[ParentMOC]]
```

**2. Project MOC (`ProjectName MOC.md`)**

Create or update `<project-folder>/ProjectName MOC.md` using `templates/project-moc.md` as the base. Adapt the template to the actual project structure:

```markdown
---
title: ProjectName MOC
parent: <ParentContext> MOC
tags:
  - moc
  - <project-tag>
---

# ProjectName MOC

Context map of **ProjectName** — <1-2 sentence description>.

## Project

- [[ProjectName]] — project page (stack, domain, server path, database)

## Wiki

- [[00-Overview|Overview]] — ...
- [[01-SRS|SRS]] — ...
- ... (all root pages)

### Module pages

- [[Modules/ControllerA|ControllerA]] — ...
- [[Modules/ModelA|ModelA]] — ...
- ... (grouped by category: Controllers, Models, Mail, Requests, Infrastructure, Views)

### Diagrams

- [[Diagrams/01-Context|Context]] · [[Diagrams/02-Container|Container]] · ...
- ... (all 14 diagrams)

### Decisions

- [[Decisions/ADR-01-...|ADR-01: ...]] · [[Decisions/ADR-02-...|ADR-02: ...]]
- ... (all ADRs)

## Wiki infrastructure

- [[10-Logbook]] — work log
- `Project.base` — Obsidian Base queryable
- `wiki-config.json` — steering
- `project-manifest.json` — metadata + last_indexed

## Stack

- **Framework:** ...
- **Language:** ...
- **Database:** ...
- **Domain:** ...
- **Hosting:** ...
- **CDN/Proxy:** ...

## Relationships

- [[ParentContext MOC]] — origin context
- [[RelatedProject]] — ...
```

**3. Update parent context MOC**

Find the parent context MOC (e.g., `Tech2Move MOC.md`) and update its project list to include the new project with links to its page, MOC, and wiki:

```markdown
- [[ProjectName]] — <short description> · [[ProjectName MOC|MOC]] · [[00-Overview|wiki]]
```

If the project already has an entry but without MOC/wiki links, update it. If the parent MOC does not exist, create it using `templates/context-map.md`.

**Completion criterion:** project page exists with quick facts and wiki links, project MOC exists with links to all modules/functions/diagrams/decisions, and parent context MOC links to all three (page, MOC, wiki).

#### Step 17 — Effort levels (Depth control)

DeepWiki (cloud) offers three effort levels controlling analysis depth.
This skill supports the same via the `effort` field in `wiki-config.json`:

| Effort | Depth | Pages | Diagrams | Functions | TechDebt | Time |
|--------|-------|-------|----------|-----------|----------|------|
| `low` (default) | Summary + architecture | 5-10 root pages | 4 key diagrams (Context, Container, Component, Flow) | Index only (no per-function pages) | Skip | Fast |
| `medium` | + modules + database | 10-20 root + module pages | 8 diagrams | Top 10-20 functions get pages | Summary only | Moderate |
| `high` | Full SRS/ISO rigor | All 30+ pages | All 14 diagrams | All public functions get pages | Full analysis | Slow |

**Behavior by effort level:**

- `low`: Skip Steps 4 (SRS), 10 (Glossary), 11 (Decisions) unless explicitly
  requested. Produce Overview, Architecture, Database, Modules index, and 4
  key diagrams only. No per-function pages — just the `05-Functions.md`
  registry table. Skip Step 18 (Deep Research) and Step 19 (TechDebt).
- `medium`: All root pages (00-10), all module pages, 8 diagrams, top 10-20
  functions by complexity/callers get individual pages. Step 18 produces a
  summary only. Step 19 produces `11-TechDebt.md` with top issues.
- `high`: Full rigor — all steps, all 14 diagrams, all public functions get
  pages, full Deep Research pass, full TechDebt analysis. This is the
  current default behavior (backward compatible — if `effort` is absent,
  treat as `high`).

Set effort in `wiki-config.json`:
```json
{
  "effort": "medium",
  "mode": "comprehensive",
  "language": "en",
  ...
}
```

If `effort` is absent, default to `high` (preserves existing behavior).

#### Step 18 — Deep Research pass (Architecture critique)

DeepWiki's Deep Research Mode "dives deeper into the codebase, identifying
potential issues, optimization opportunities, and architectural critiques,
functioning similarly to a senior code reviewer."

This step is **optional** — skipped at `low` effort, summary-only at
`medium`, full at `high`. It runs AFTER all documentation pages are built,
so the critique is grounded in the documented architecture.

**Procedure:**

1. Read `02-Architecture.md` and all `Modules/*.md` pages.
2. For each module, evaluate against `architecture` principles:
   - **Depth**: are there shallow modules that should be deeper?
   - **Leverage**: does a low-leverage module force changes in many dependents?
   - **Locality**: are related concerns co-located, or scattered?
   - **Seams**: are seams clean (testable, swappable) or leaky?
   - **Adapters**: are external dependencies isolated behind adapters?
3. Identify anti-patterns:
   - God modules (high fan-in + high fan-out)
   - Circular dependencies
   - Shotgun surgery (one change touches >5 files)
   - Primitive obsession (everything is strings/ints instead of domain types)
   - Dead code (modules with no inbound links in the wiki)
4. Identify optimization opportunities:
   - Obvious performance bottlenecks (N+1 queries, sync I/O in hot paths)
   - Missing tests for critical paths (cross-reference `05-Functions.md` Tests column)
   - Config hardcoding (values that should be env vars)
   - Dependency risks (outdated, unmaintained, or duplicate packages)
5. Produce findings as cited claims — every issue MUST cite the source
   file and line where the anti-pattern or issue is visible.

**Output:** findings are written to `11-TechDebt.md` (Step 19) and
summarized in the Architecture page's `## Architecture critique` section
(if `high` effort).

**Rigor note:** this step does NOT modify code. It documents issues only.
Fixing issues is a separate task that should use `debugging` or
`code-review` skills.

#### Step 19 — Tech Debt page (`11-TechDebt.md`)

Create a page documenting issues found in Step 18. This is the local
equivalent of DeepWiki's issue identification.

```markdown
---
title: "Project - Tech Debt"
project: "Project Name"
parent: 00-Overview
tags:
  - tech-debt
  - architecture
status: active
---

# Tech Debt and Improvement Opportunities

## Relevant source files
- `source: src/` (all modules analyzed)
- `source: tests/` (coverage analysis)

## Purpose and Scope
Issues, anti-patterns, and optimization opportunities identified during
the Deep Research pass. Each item is cited to source.

## Anti-patterns

### AP-001: <anti-pattern name>
- **Type:** God module | Circular dep | Shotgun surgery | ...
- **Location:** `source: src/module/file.ts:42`
- **Impact:** <what breaks if this isn't fixed>
- **Recommendation:** <suggested approach>
- **Effort to fix:** Low | Medium | High

## Optimization opportunities

### OPT-001: <opportunity name>
- **Type:** Performance | Test coverage | Config | Dependency
- **Location:** `source: src/module/file.ts:88`
- **Current:** <what it does now>
- **Recommended:** <what it should do>
- **Expected gain:** <measurable improvement>

## Dependency risks

| Package | Version | Risk | Source |
|---------|---------|------|--------|
| `lodash` | 4.17.20 | Outdated (CVE-2021-23337) | `source: package.json:23` |

## Missing tests

| Function | Criticality | Source | Test file |
|----------|-------------|--------|-----------|
| `processPayment` | High | `source: src/payments.ts:45` | (none found) |

Sources: src/, tests/, package.json
```

**Quality requirements:**
- Every issue MUST have a `source: path:line` citation (Rule 17 — no
  deductions about code without reading it)
- Every anti-pattern MUST be categorized (type, impact, recommendation,
  effort)
- Issues are numbered (AP-001, OPT-001) for traceability
- The page links back to `[[02-Architecture]]` and `[[04-Modules]]`

**Update `00-Overview.md`** to include a wikilink to `[[11-TechDebt]]`.
**Update the project MOC** to include `[[11-TechDebt|Tech Debt]]` in the
Wiki section.

#### Step 20 — Conversational Q&A integration

DeepWiki integrates with Ask Devin for conversational Q&A over the wiki.
The local equivalent chains `query.py` (keyword search) with the
`research` skill (multi-pass agentic search with citations).

**For simple lookups:**
```bash
python <vault-dir>/query.py --query "authentication flow"
```

**For deep questions over the wiki** (equivalent to Ask Devin + DeepWiki):
1. Invoke the `research` skill with the wiki directory as the search scope
2. `research` runs its 4-pass search (broad sweep -> deep read ->
   cross-file synthesis -> architecture map) over the wiki `.md` files
3. Every finding cites wiki page + original source file (double citation:
   wiki page that documents the code, and the code file itself)

**Example:**
```
User: "How does the authentication flow work in this project?"

Agent: [invokes deep-mode skill scoped to <vault-dir>/_wiki/]
  Pass 1: grep for "auth" across _wiki/*.md -> finds 02-Architecture.md,
          Modules/Auth.md, 05-Functions.md, Diagrams/07-Sequence.md
  Pass 2: read those wiki pages -> extracts documented auth flow
  Pass 3: cross-reference with source files cited in the wiki pages
  Pass 4: produce narrative with citations to both wiki and source

Output:
  "The auth flow uses OAuth2 with JWT [wiki: Modules/Auth.md:15,
   source: src/auth/oauth.ts:23]. The middleware checks expiry
  [wiki: 02-Architecture.md:42, source: src/middleware/auth.ts:58]..."
```

This gives the CLI a conversational Q&A experience over the wiki that
approximates DeepWiki + Ask Devin in the cloud.

## Deviation / exceptions

- If the project is not a software project, fall back to `grilling` (With-docs mode) or `knowledge-modeling`.
- If the user only wants diagrams, use `references/modern-diagrams.md` and skip the SRS.
- If the user only wants a database schema, use `03-Database.md` and the `Modules/Database/` notes.
- If there is no parent context MOC (standalone project), skip step 3 of Step 16.

## Quality checklist

- [ ] **Information sources confirmed** — the user was asked (Step 0.5) whether the codebase is sufficient or additional context is needed. User-provided context saved in `wiki-config.json` `repo_notes` with `author: "user"`.
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
- [ ] `10-Logbook.md` links to every `Daily/YYYY-MM-DD.md` entry.
- [ ] Daily notes capture context, done, tried, worked, failed, decisions, rationale and next actions.
- [ ] **Root pages (00-09, 10-Logbook) have standardized frontmatter**: `title` ("Project - Page", hyphen not em-dash), `project`, `parent`, `tags` (YAML list), `status` (active/inactive).
- [ ] **Daily notes have standardized frontmatter**: `title` ("Project - YYYY-MM-DD", hyphen), `date`, `project`, `parent: 10-Logbook`, `tags` (YAML list with logbook + project tag), `status` (active/inactive).
- [ ] All internal references use Obsidian wikilinks `[[...]]`.
- [ ] Wiki content is in the `language` specified in `wiki-config.json`.
- [ ] **Project page (`ProjectName.md`) exists** as a sibling of `_wiki/` with quick facts table, core features list, and wiki links to all root pages.
- [ ] **Project MOC (`ProjectName MOC.md`) exists** with links to the project page, all root wiki pages, all module pages (grouped by category), all diagrams, and all ADRs. Uses `templates/project-moc.md` as base.
- [ ] **Parent context MOC updated** to link to this project's page, MOC, and wiki (`[[ProjectName]] — desc · [[ProjectName MOC|MOC]] · [[00-Overview|wiki]]`). If no parent MOC exists, this is skipped (standalone project).
- [ ] **`02-Architecture.md` has a `## Diagrams` section** with wikilinks to all 14 `Diagrams/*.md` files. Without this, diagrams are graph orphans.
- [ ] **`05-Functions.md` registry table uses `[[Functions/<name>|<name>]]` wikilinks** in the Function column — not plain text. Without this, function pages are graph orphans.
- [ ] **Function pages have a `## Links` section** linking back to `[[05-Functions]]` and `[[Modules/<parent>]]`.
- [ ] **MOC ADR references use full filename stems** (e.g. `[[Decisions/ADR-01-slug|ADR-01: Title]]`), not short forms (`[[Decisions/ADR-01]]` — file doesn't exist).
- [ ] **`00-Overview.md` links to ALL root pages** (01-SRS through 10-Logbook), not just a subset. Every root page must have at least one inbound link.
- [ ] **Zero graph orphans** — run `scripts/find_orphan_pages.py --wiki <wiki-dir>` and verify 0 orphan pages (no inbound AND no outbound wikilinks).
- [ ] **Content rigor validated** — run `scripts/validate_wiki_content.py --wiki-dir <wiki-dir>` and verify 0 failures (source format, min 5 sources, footers, overview links, function links, source columns, TechDebt content, arch critique, effort valid).
- [ ] **Effort level respected** — if `wiki-config.json` has `effort: low`, Steps 4/10/11/18/19 are skipped. If `medium`, Step 18 is summary-only. If `high` or absent, all steps run (backward compatible).
- [ ] **`11-TechDebt.md` exists** (effort: medium/high) — every issue has `source: path:line` citation, every anti-pattern is categorized (type, impact, recommendation, effort), issues are numbered (AP-001, OPT-001).
- [ ] **`00-Overview.md` links to `[[11-TechDebt]]`** (effort: medium/high) — TechDebt page is not a graph orphan.
- [ ] **Architecture critique section** (effort: high only) — `02-Architecture.md` has a `## Architecture critique` section summarizing Deep Research findings with source citations.
- [ ] **Conversational Q&A** — `query.py` works for keyword search; `research` skill can be invoked scoped to the wiki directory for multi-pass agentic search with double citations (wiki + source).

## Templates and references (Build Wiki)

- `templates/srs-template.md`
- `templates/module-template.md`
- `templates/database-template.md`
- `templates/config-template.md`
- `templates/function-template.md`
- `templates/daily-note-template.md`
- `templates/overview-template.md`
- `templates/adr-template.md`
- `templates/project-moc.md`
- `references/obsidian-bases-spec.md`
- `references/modern-diagrams.md`

## Validation scripts (Build Wiki)

| Script | Purpose | When to run |
|--------|---------|-------------|
| `scripts/scaffold.py` | Create vault structure (pages, diagrams, configs) | Step 1 — initial scaffold |
| `scripts/validate_wiki_structure.py` | Structural checks (16+3 checks: files, dirs, frontmatter, diagrams, links, secrets, effort, TechDebt, arch critique) | After build, before commit |
| `scripts/validate_wiki_content.py` | Content rigor checks (9 checks: source format, min 5 sources, footers, overview links, function links, source columns, TechDebt content, arch critique, effort valid) | After build, before commit |
| `scripts/find_orphan_pages.py` | Graph orphan detection (no inbound AND no outbound wikilinks) | After build, before commit |
| `scripts/audit.py` | Full audit (diagrams, mermaid syntax, frontmatter, links, sources %, language, secrets) | Periodic / before sync |
| `scripts/validate_links.py` | Wikilink validation only | Quick link check |
| `scripts/validate_mermaid.py` | Mermaid syntax validation only | Quick diagram check |
| `scripts/scan_secrets.py` | Sensitive information scan only | Security audit |
| `scripts/fix_templates.py` | Fix broken template links | When audit finds template issues |

---
