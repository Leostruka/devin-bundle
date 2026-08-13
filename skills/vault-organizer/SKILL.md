---
name: vault-organizer
description: Use when the user wants to reorganize, refactor, or restructure an Obsidian vault, knowledge base, or documentation folder — diagnosing organizational problems, selecting appropriate methodologies, and planning or executing a safe refactoring.
triggers:
- user
- model
---
# Vault Organizer

Diagnose organizational problems in a knowledge base (Obsidian vault, docs folder, wiki), select methodologies that fit the specific content, and plan a safe refactoring — then execute with wikilink validation. The skill is **adaptive**: it judges what structure to recommend based on what actually exists, not a fixed template.

**Scope:** Obsidian vaults, documentation folders, project wikis, any hierarchical knowledge base with files and folders.

## When to use

- "Reorganize my vault"
- "This vault is a mess, help me structure it"
- "Plan a refactoring of my documentation"
- "My projects are scattered, organize them"
- "Audit my knowledge base structure"
- After a merger or acquisition that combined multiple knowledge bases
- When a vault has grown organically and needs structural correction

## Workflow

### Step 1 — Scan the target

Map the complete structure of the target directory.

1. Run `tree` or `ls -R` (or `Get-ChildItem -Recurse` on Windows) to get the full directory tree.
2. For each `.md` file, read the first 20 lines to capture frontmatter and H1/H2 headers.
3. Record: file count, folder depth, frontmatter fields in use, tag taxonomy if any.
4. Identify what type of content lives here: projects, companies, personal notes, code docs, research, etc.
5. If the vault is large (> 100 files), consider dispatching a `subagent_explore` to scan in parallel.

**Completion criterion:** you have a complete inventory of every file and folder, with headers and frontmatter captured, and can describe what the vault contains in 2-3 sentences.

### Step 2 — Diagnose organizational problems

Compare the scanned structure against the diagnosis patterns in `references/diagnosis-patterns.md`. For each pattern, check whether it applies to the current vault.

The patterns detect common organizational smells:
- **Orphaned content** — files documenting a specific project but located outside that project's folder
- **Scattered project** — components of one project spread across multiple unrelated directories
- **Shared resources lost** — infrastructure that serves multiple projects but is isolated in one
- **Misplaced entity** — a distinct entity nested inside another
- **Loose notes** — standalone files at the root with no context
- **Mixed active/archived** — abandoned projects at the same level as active ones
- **Inconsistent structure** — different areas use different organizational schemes
- **Missing metadata** — no `title` field, no standard frontmatter, no MOCs

**Completion criterion:** every diagnosis pattern has been checked, and you have a numbered list of confirmed problems with concrete examples from the scan.

### Step 3 — Select methodologies

Read `references/methodologies.md` — a library of 10 academically-grounded organization methodologies. For each methodology, check its **decision criteria** against what you found in the scan.

The selection is adaptive: different vaults need different combinations. A personal Zettelkasten needs different methods than a multi-company project vault. A research notebook needs different methods than a software documentation folder.

Selection heuristics (full criteria in `references/methodologies.md`):
- **Multiple distinct entities with different terminology** → DDD Bounded Contexts
- **Projects scattered across directories** → Every Folder is a Project
- **Wikilink-based system (Obsidian)** → MOC (Map of Content)
- **Items belonging to multiple categories** → Polyhierarchical Faceted Tags
- **Need for strict discipline and memorability** → Johnny.Decimal
- **Knowledge connections over categories** → Zettelkasten
- **Archival and preservation needs** → OAIS
- **Complex multi-dimensional content** → Information Architecture (faceted)
- **Classification is not neutral / boundary objects** → Bowker and Star (critical lens)

Typically 2-4 methodologies combine, each solving a different class of problem. Document why each was selected and which diagnosed problems it addresses.

**Completion criterion:** you have a recommendation table mapping each selected methodology to its role and the specific problems it solves.

### Step 4 — Design the target structure

Based on the selected methodologies and diagnosed problems, design the new structure.

1. Draw the proposed folder tree.
2. For each new folder, state its purpose and which methodology informed it.
3. Design a tag taxonomy if polyhierarchical tags were selected.
4. Design MOC hub notes if MOC was selected.
5. Design frontmatter template for new and updated files (see `templates/frontmatter.md`).
6. List files and folders that should NOT be moved (e.g., `.obsidian/`, config).

Present the design to the user with `ask_user_question` before proceeding to the move plan.

**Completion criterion:** the user has approved the target structure.

### Step 5 — Plan the refactoring

Generate a move plan mapping every file from old location to new location.

1. For each file, determine its destination in the new structure.
2. Record the problem each move solves (from Step 2).
3. Identify files that need new MOC or index notes created.
4. Identify files that should NOT be moved (explicit "preserve" entries).
5. Group moves into phases:
   - Phase 1: Create new folder structure
   - Phase 2: Move projects (group by entity)
   - Phase 3: Move shared resources
   - Phase 4: Create MOCs and index notes
   - Phase 5: Move loose notes and archived content

Present the plan as a table: `Origin → Destination → Problem solved`.

**Completion criterion:** every file has a planned destination (or explicit "preserve"), and the plan is grouped into phases.

### Step 6 — Execute the refactoring

Execute the plan phase by phase. Use `ask_user_question` to confirm before starting execution.

1. Create the new folder structure.
2. Move files using `mv` or `Move-Item`.
3. Create MOC hub notes from `templates/project-moc.md` and `templates/context-map.md`.
4. Apply frontmatter updates where needed.
5. After each phase, verify the moves succeeded (check file counts).

Guardrails:
- Do NOT delete any files — only move and create.
- Do NOT rewrite existing file contents — only move and create new index/MOC files.
- Preserve existing frontmatter fields — only add new ones if the design requires.

**Completion criterion:** all phases executed, all files in their planned destinations, no files lost.

### Step 7 — Validate wikilinks and references

After all moves:

1. Grep for `[[...]]` wikilinks across all `.md` files.
2. For each wikilink, check if the target file exists at the expected path.
3. Report broken links and suggest fixes.
4. If Obsidian, check that `.obsidian/` config is intact.
5. Run a final tree to confirm the structure matches the design.

**Completion criterion:** zero broken wikilinks, or all broken links listed with proposed fixes for user confirmation.

### Step 8 — Generate a refactoring report

Create a summary document (e.g., `REFACTORING-LOG.md` in the vault root) recording:
- Date of refactoring
- Methodologies selected and why
- Problems diagnosed and resolved
- Move count per phase
- Files created (MOCs, indexes)
- Validation results
- Tag taxonomy applied (if any)

**Completion criterion:** the report exists and accurately reflects what was done.

## Running with graphify

If the vault is large or complex, run `graphify <vault-dir> --no-viz` before Step 1. Use the resulting graph to identify:
- Clusters of related files
- Orphaned nodes (files with no incoming links)
- Hub nodes (files referenced by many others)

This accelerates diagnosis and helps validate the move plan.

## Deviation and exceptions

- If the vault is small (< 20 files), skip the methodology selection and apply common-sense organization directly.
- If the user only wants a diagnosis (no execution), stop after Step 5 and present the plan.
- If the vault is not Obsidian (plain docs folder), skip wikilink validation and MOC creation — use `README.md` indexes instead.
- If the user wants to preserve specific files or folders, exclude them from the move plan explicitly.
- If the vault uses a non-Markdown format (Notion export, Roam, etc.), adapt the scan and validation steps accordingly.

## Templates and references

- `references/methodologies.md` — library of 10 organization methodologies with decision criteria
- `references/diagnosis-patterns.md` — organizational problem patterns and detection heuristics
- `templates/project-moc.md` — MOC template for individual projects
- `templates/context-map.md` — context map template for domains and entities
- `templates/frontmatter.md` — frontmatter template for organized files
