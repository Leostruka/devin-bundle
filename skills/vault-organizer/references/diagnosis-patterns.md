# Diagnosis patterns — organizational problems and detection heuristics

8 patterns of organizational dysfunction in knowledge bases. Each pattern has a **detection heuristic** — how to identify it during a scan — and a **resolution direction** — which methodologies address it.

## How to use

During Step 2 of the skill, check each pattern against the scanned vault. A pattern is confirmed when its detection heuristic matches concrete evidence from the scan. Record each confirmed problem with a specific example.

---

## P1 — Orphaned content

**Description:** Files that document a specific project or entity but are located outside that project's folder. The content belongs to X but lives in Y's directory.

**Detection heuristic:**
- Read file headers and frontmatter. If a file's content references project/entity A but is located in entity B's folder, it is orphaned.
- Look for `_wiki/`, `docs/`, or similar documentation folders at a higher level than the project they document.
- Grep for frontmatter fields like `project:`, `empresa:`, `context:` and compare against the file's actual path.

**Example:** `_wiki/` is at `Fingertech/_wiki/` but its content documents only `Site Fingertech` — it should be inside `Fingertech/projetos/Site Fingertech/`.

**Resolution direction:** Every Folder is a Project (move docs into the project folder) + MOC (create a project MOC that links to the docs).

---

## P2 — Scattered project

**Description:** Components of a single project spread across multiple unrelated directories. One product, multiple folder homes.

**Detection heuristic:**
- Identify projects by name (grep for project names in headers, frontmatter, and content).
- For each project name, list all directories where its files appear.
- If a project's files appear in 2+ top-level unrelated directories, it is scattered.
- Look for patterns like `web/externo/comercializado/X/`, `nativo/extensao/X/`, `nativo/mobile/X/` — same product, three directories.

**Example:** "Trinity Smart Point" has web in `web/externo/comercializado/`, extension in `nativo/extensao/`, and Android in `nativo/mobile/` — 3 directories for 1 product.

**Resolution direction:** Every Folder is a Project (consolidate into one folder) + MOC (create a product-level MOC linking all components).

---

## P3 — Shared resources lost

**Description:** Infrastructure, databases, servers, or APIs that serve multiple projects/entities but are isolated inside one entity's folder.

**Detection heuristic:**
- Look for folders named `db/`, `infra/`, `servers/`, `shared/` inside entity-specific directories.
- Read the content of files in those folders — if they reference multiple entities or projects, they are shared resources trapped in one entity's scope.
- Grep for mentions of multiple entity names in infrastructure files.

**Example:** `Fingertech/db/Google Cloud SQL Server.md` serves Trinity-ERP, ML_CRM, and FingerNET — but is isolated under Fingertech only.

**Resolution direction:** DDD Bounded Contexts (shared resources get their own context) + Polyhierarchical Tags (tag with `serves/fingertech`, `serves/tech2move` for multi-entity access).

---

## P4 — Misplaced entity

**Description:** A distinct entity (company, brand, team, domain) nested as a subfolder inside another entity. The nested entity should be a peer, not a child.

**Detection heuristic:**
- List all top-level entity directories and their immediate children.
- If a child directory contains a complete, self-contained entity structure (its own projects, its own infra, its own MOC), it is a misplaced entity.
- Check frontmatter — if files in the child directory have a different `empresa:` or `context:` value than the parent, the entity is misplaced.

**Example:** `Fingertech/stepover/` is a separate brand with its own projects, but is nested as a subfolder of Fingertech instead of being a peer at the root.

**Resolution direction:** DDD Bounded Contexts (promote to a top-level context) + Every Folder is a Project (reorganize projects within the promoted entity).

---

## P5 — Loose notes

**Description:** Standalone files at the vault root or in unrelated folders, with no project context, no parent MOC, and no clear home.

**Detection heuristic:**
- List all files at the vault root (not inside any folder).
- Check if each root-level file has frontmatter linking it to a project or entity.
- Files with no `project:`, no `empresa:`, no `parent:`, and no folder context are loose notes.
- Also check for files in catch-all folders like `misc/`, `outros/`, `varios/` — these are often loose notes that were swept into a temporary home.

**Example:** `DFDU500P (D-Plus).md`, `Instalação qt4 linux antigos.md`, `Links Úteis Suporte.md` — all at the vault root with no context.

**Resolution direction:** MOC (create a knowledge base MOC for orphaned reference material) + IA faceted classification (tag by type: `tipo/driver`, `tipo/suporte`, `tipo/referencia`).

---

## P6 — Mixed active and archived

**Description:** Abandoned or archived projects at the same directory level as active projects. No clear separation between live and dead content.

**Detection heuristic:**
- Look for folders named `_abandonado/`, `_old/`, `_deprecated/`, `_archive/` at the same level as active project folders.
- Check frontmatter for `status:` fields — if some files have `status: abandoned` or `status: archived` but are mixed with `status: active` files in the same directory, the pattern applies.
- Look for projects with no recent modifications (check file mtime) sitting alongside actively maintained projects.

**Example:** `_abandonado/` folder at the same level as `web/`, `api/`, `nativo/` — archived content mixed with active development.

**Resolution direction:** OAIS-inspired (separate `_arquivo/` per entity) + Polyhierarchical Tags (`#status/arquivado` for filtering) + MOC (Arquivados MOC linking all archived content).

---

## P7 — Inconsistent structure

**Description:** Different areas of the vault use different organizational schemes. One entity has `web/api/nativo/db/infra`, another has only `web/wavlink`, a third has `web/marca`.

**Detection heuristic:**
- For each top-level entity directory, list its immediate children.
- Compare the folder structures — if entities use different naming conventions, different depths, or different organizational axes, the structure is inconsistent.
- Check if some entities have subfolders that others don't (e.g., one has `infra/` but another doesn't, even though both have infrastructure).

**Example:** Fingertech has `web/api/nativo/db/infra`, Tech2Move has `web/wavlink`, LDNTech has `web/marca` — three different schemes for similar content.

**Resolution direction:** Every Folder is a Project (standardize on `projetos/` as the common subfolder) + DDD Bounded Contexts (each entity has the same internal structure: `MOC + projetos/ + infra/ + _arquivo/`).

---

## P8 — Missing metadata

**Description:** Files lack standard frontmatter fields. No `title:` field, no consistent tagging, no MOCs to serve as navigation hubs.

**Detection heuristic:**
- Sample 10-20 `.md` files across different folders. Check their frontmatter.
- If the majority lack a `title:` field, the pattern applies.
- If there are no files with "MOC" in their name or `type: moc` in frontmatter, MOCs are missing.
- If tags are used inconsistently (some files have tags, others don't, and the tag format varies), tagging is missing.

**Example:** No file in the vault has a `title:` field. Tags are used in some files but with inconsistent formats (`#fingertech` vs `#empresa/fingertech`).

**Resolution direction:** MOC (create MOC hub notes for each entity and project) + Polyhierarchical Tags (design a standard tag taxonomy) + IA faceted classification (standardize frontmatter fields).

---

## Pattern summary table

| Pattern | Key signal | Primary methodology |
|---|---|---|
| P1 Orphaned content | Docs outside their project folder | Every Folder is a Project + MOC |
| P2 Scattered project | One project, multiple directories | Every Folder is a Project + MOC |
| P3 Shared resources lost | Multi-entity infra in one entity | DDD + Polyhierarchical Tags |
| P4 Misplaced entity | Entity nested inside another | DDD Bounded Contexts |
| P5 Loose notes | Root-level files with no context | MOC + IA faceted |
| P6 Mixed active/archived | Abandoned mixed with active | OAIS-inspired + Tags |
| P7 Inconsistent structure | Different schemes per entity | Every Folder is a Project + DDD |
| P8 Missing metadata | No title, no MOCs, no tag standard | MOC + Tags + IA faceted |
