---
name: obsidian-project-docs
description: Document software projects in Obsidian as an SRS/ISO-style engineering wiki. Scaffolds notes, Bases (modules, functions, dependencies, config) and Canvas architecture diagrams. Use when the user wants to build or update project documentation in an Obsidian vault, create SRS/ISO docs, map dependencies, or visualize architecture.
---

# obsidian-project-docs

Build a **meticulous, SRS/ISO-style documentation suite** for a software project inside an Obsidian vault. The skill scaffolds notes, `.base` database views, and `.canvas` diagrams, then guides the agent to fill them from code, config, and conversation.

**Scope:** dependencies, database schema, modules, functions, config files, environment variables, relationships, architecture, decisions, glossary.

## When to use

- "Document this project in Obsidian"
- "Create SRS / technical specification"
- "Build an architecture map"
- "List all modules, functions, and dependencies"
- "Visualize the system in Obsidian Canvas"
- Updating an existing engineering wiki

## What is produced

Inside the target Obsidian vault (or project subfolder) the skill creates:

| Artifact | File | Purpose |
|----------|------|---------|
| SRS | `00-SRS.md` | Software Requirements Specification — scope, stakeholders, functional/non-functional requirements |
| Architecture | `01-Architecture.md` | System overview, layers, seams, adapters, data flow, decisions |
| Database | `02-Database.md` | Schema, tables/collections, relationships, migrations, indexing |
| Modules index | `03-Modules.md` + `Modules/*.md` | Module catalog with interfaces, invariants, tests, dependencies |
| Functions index | `04-Functions.md` | Function / method registry, signatures, side effects, callers |
| Dependencies | `05-Dependencies.md` | Third-party and internal dependencies with versions and rationale |
| Config | `06-Config.md` | Environment variables, config files, feature flags, defaults |
| Glossary | `07-Glossary.md` | Domain terms from `CONTEXT.md` and the codebase |
| Project base | `Project.base` | Obsidian Base tying modules, functions, dependencies, config into a queryable database |
| Architecture canvas | `Architecture.canvas` | JSON Canvas with modules, databases, external systems and relationships |

## Quick start

```bash
# 1. Scaffold a new vault/project doc tree
python <skill-dir>/scaffold.py --project-dir C:\path\to\project --vault-dir C:\path\to\ObsidianVault\MyProject

# 2. Or into a folder inside the current project (useful for Git-tracked docs)
python <skill-dir>/scaffold.py --project-dir . --vault-dir ./docs/obsidian
```

Then invoke the rest of this skill to fill each artifact from code and conversation.

## Workflow

### Step 0 — Detect or confirm target

1. If the user gave a vault path, use it. Otherwise default to a subfolder of the current project: `<project>/docs/obsidian/`.
2. If the vault/docs folder already contains the artifact files, this is an **update** run. Read them first.
3. If the files do not exist, run the scaffold script in Step 1.

### Step 1 — Scaffold the vault

Run the scaffold helper with the project and vault directories. It creates the file tree, the Base, and the Canvas shell.

```bash
python <skill-dir>/scaffold.py --project-dir <PROJECT> --vault-dir <VAULT>
```

The helper also writes a lightweight `project-manifest.json` in the vault:

```json
{
  "project_name": "MyProject",
  "project_dir": "C:/path/to/project",
  "vault_dir": "C:/path/to/ObsidianVault/MyProject",
  "created": "2026-08-11",
  "version": "0.1.0"
}
```

### Step 2 — Build the SRS (`00-SRS.md`)

Read any existing README, specs, issues, or conversation context. Fill each section of `00-SRS.md`:

- Purpose and scope
- Stakeholders and actors
- Functional requirements (numbered, testable)
- Non-functional requirements (performance, security, reliability)
- Constraints and assumptions
- Acceptance criteria

Use callouts for risk or open questions:

```markdown
> [!warning] Open question
> The failover strategy is not yet defined.
```

### Step 3 — Architecture (`01-Architecture.md`)

Use the `codebase-design` vocabulary (module, interface, seam, adapter, depth, leverage, locality). Document:

- Architectural drivers
- Layers and modules
- Seams and adapters
- Data flow
- External integrations
- ADRs

### Step 4 — Database (`02-Database.md`)

For each database / persistence layer:

- Technology and version
- Schema overview
- Tables / collections with purpose
- Columns / fields, types, constraints, indexes
- Relationships (ER-style or wikilinks)
- Migrations strategy
- Backup / replication notes

### Step 5 — Modules and Functions catalog

For each module:

1. Create or update `Modules/<ModuleName>.md` from `templates/module-template.md`.
2. Extract from code:
   - interface (public functions, classes, exported symbols)
   - invariants and ordering constraints
   - error modes
   - dependencies (internal and external)
   - tests
3. Update the central `03-Modules.md` index with a table and wikilinks.

For functions:

1. Scan the codebase for exported / public functions.
2. In `04-Functions.md`, build a registry table:
   - Function, Module, Signature, Side effects, Calls, Tests
3. For critical functions, create detailed sub-notes.

### Step 6 — Dependencies (`05-Dependencies.md`)

Read package managers and config files (`package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, etc.). List:

- Production dependencies (name, version, purpose, license if known)
- Development dependencies
- Internal dependencies (cross-module imports)
- Optional / runtime dependencies
- Deprecated or risky dependencies

### Step 7 — Config (`06-Config.md`)

Collect config artifacts:

- Environment variables (from `.env.example`, `docker-compose.yml`, code, docs)
- Config files (`*.config.*`, `*.json`, `*.yaml`, `*.toml`, `*.ini`)
- Feature flags and defaults
- Secrets management strategy

### Step 8 — Glossary (`07-Glossary.md`)

Use `domain-modeling` discipline. Copy or extend `CONTEXT.md` terms. Add:

- Domain term
- Definition
- Synonyms / aliases
- Where it appears in code

### Step 9 — Build / update the Project Base (`Project.base`)

The `.base` file ties everything together. Populate it with rows for modules, functions, dependencies, and config. Each row is an Obsidian note linked by `file.path`.

See `references/obsidian-bases-spec.md` for Base syntax.

### Step 10 — Build / update the Architecture Canvas (`Architecture.canvas`)

Create a JSON Canvas with:

- Modules as text or file cards
- Databases as groups or cards
- External systems as link or text cards
- Edges showing imports, calls, data flow
- Color coding: green for modules, purple for databases, yellow for external systems

See `references/json-canvas-spec.md` for Canvas syntax.

You may also use `graphify` first to extract the code graph and then translate key nodes and edges into the Canvas.

## Running with graphify

If the project has many files, run `/graphify <project-dir> --no-viz` before documenting. Use the resulting `graphify-out/graph.json` and `GRAPH_REPORT.md` to identify:

- Modules and communities
- Dependency edges
- Central vs peripheral nodes
- Unresolved or ambiguous relationships

Then write the findings into the Obsidian vault using this skill.

## Deviation / exceptions

- If the project is not a software project, fall back to `grill-with-docs` or `domain-modeling`.
- If the user only wants a Canvas, use `references/json-canvas-spec.md` and skip the SRS.
- If the user only wants a database schema, use `02-Database.md` and the `Modules/Database/` notes.

## Quality checklist

- [ ] Every module has a `Modules/*.md` note with interface and dependencies.
- [ ] Every functional requirement in `00-SRS.md` is traceable to a module or function.
- [ ] `05-Dependencies.md` matches the package manager files.
- [ ] `06-Config.md` includes all env vars and config files.
- [ ] `Project.base` renders as a table in Obsidian.
- [ ] `Architecture.canvas` has no dangling edges and all nodes are readable.
- [ ] All internal references use Obsidian wikilinks `[[...]]`.

## Templates

- `templates/srs-template.md`
- `templates/module-template.md`
- `templates/database-template.md`
- `templates/config-template.md`
- `templates/function-template.md`
- `references/json-canvas-spec.md`
- `references/obsidian-bases-spec.md`
