# Organization methodologies library

10 academically-grounded methodologies for organizing knowledge bases. Each entry has **decision criteria** — the conditions that make it a good fit for a given vault. Use these criteria to select which methodologies to combine for a specific refactoring.

## How to use this library

1. After scanning and diagnosing the vault (Steps 1-2 of the skill), read each methodology's decision criteria.
2. Check whether the criteria match what you found in the vault.
3. Select 2-4 methodologies that complement each other — each solving a different class of problem.
4. Document why each was selected and which diagnosed problems it addresses.

No single methodology solves every problem. The power is in the combination.

---

## 1. Information Architecture (IA)

**Origin:** Rosenfeld and Morville, "Information Architecture for the World Wide Web" (O'Reilly, 1998-2014). Faceted classification based on S.R. Ranganathan's colon classification.

**Principle:** Organization Schemes (Exact vs Ambiguous) + Organization Structures (Hierarchical, Database-oriented, Hypertext) + Faceted Classification.

**Decision criteria — use when:**
- Content is multi-dimensional (can be described along several independent axes)
- Users need to find items via different paths (by project, by technology, by status, by team)
- A pure hierarchy forces awkward placements (items that belong in two places)
- The vault has or could benefit from metadata-driven search/filter

**Role in a combination:** Provides the faceted classification framework — usually implemented via tags or frontmatter, not folders. Pairs with a hierarchical primary structure from another methodology.

**Strengths:** Handles multi-dimensional content; faceted approach allows multiple access paths without duplication.
**Weaknesses:** Requires upfront design of taxonomy and metadata schema; can be complex to maintain.

---

## 2. TRUST / FAIR Principles

**Origin:** TRUST Principles (Nature Scientific Data, 2020); FAIR Principles (FORCE11, 2016); InterPARES project.

**Principle:** Transparency, Responsibility, User focus, Sustainability, Technology (TRUST). Findable, Accessible, Interoperable, Reusable (FAIR).

**Decision criteria — use when:**
- Long-term preservation is a goal
- Content needs to be discoverable by people outside the original team
- Interoperability with other systems matters
- The vault contains research data or archival material

**Role in a combination:** Overlay of preservation principles on top of a structural methodology. Not a primary organizing structure.

**Strengths:** Ensures long-term sustainability and findability.
**Weaknesses:** Not a structural methodology by itself; best as an overlay.

---

## 3. OAIS Reference Model (ISO 14721)

**Origin:** CCSDS, ISO 14721:2012/2025. Reference Model for an Open Archival Information System.

**Principle:** Information Packages (SIP → AIP → DIP) + Preservation Description Information (Reference, Context, Provenance, Fixity, Access Rights) + 6 Functional Entities.

**Decision criteria — use when:**
- The vault has a significant portion of abandoned or archived projects
- Long-term preservation with provenance tracking is needed
- There are regulatory or compliance requirements for record retention
- Archived content needs to be clearly separated from active content

**Role in a combination:** Manages the archival portion of the vault. Active projects use a different methodology; archived projects get OAIS-style treatment (provenance, fixity, access rights metadata).

**Strengths:** Gold standard for digital preservation; comprehensive provenance tracking.
**Weaknesses:** Overkill for active projects; heavy metadata requirements. For most vaults, a simpler `_arquivo/` folder with `#status/arquivado` tags suffices.

---

## 4. Johnny.Decimal System

**Origin:** Johnny.Decimal.com (2019-present). A personal organization system with AC.ID notation.

**Principle:** Areas (10-19, 20-29...) → Categories → IDs. Every item has exactly one ID. JDex (index) for cross-referencing. Standard Zeros for inbox/temp.

**Decision criteria — use when:**
- The vault is small to medium (up to a few hundred items)
- Strict discipline and memorability are valued
- Each item has a clear single home (no multi-categorization needed)
- Numeric IDs would aid navigation and recall

**Role in a combination:** Provides the folder naming convention and index. Can conflict with polyhierarchical needs — use only when items have a single natural home.

**Strengths:** Simple, memorable, forces discipline, index for cross-referencing.
**Weaknesses:** Single location per item (no polyhierarchy); requires index maintenance; rigid for evolving content.

---

## 5. Zettelkasten Method

**Origin:** Niklas Luhmann, German sociologist (1927-1998). 30+ years of development, 90,000+ notes.

**Principle:** No categories (deliberate rejection of topical classification). Fixed filing place (each note has a unique ID and never moves). Linkage over folders — bidirectional links connect notes across topics. Keyword index for discovery.

**Decision criteria — use when:**
- The vault is a personal knowledge base focused on ideas and connections
- Content is interdisciplinary (notes span many domains)
- The user values emergent structure over designed structure
- Scale is large (thousands of notes) and growing
- The primary access pattern is via links, not folder browsing

**Role in a combination:** Provides the linking philosophy. Pairs well with MOC for navigation. Rejects folder-based organization as primary structure — links are the structure.

**Strengths:** Perfect for interdisciplinary connections; structure emerges from use; scales to 90,000+ notes; aligns with Obsidian's wikilink architecture.
**Weaknesses:** Requires linking discipline; no obvious structure for newcomers; keyword index needs maintenance; not suited for project-based organization.

---

## 6. MOC (Map of Content) Pattern

**Origin:** LYT (Linking Your Thinking) framework by Nick Milo. Obsidian community standard.

**Principle:** MOC as a hub note — a curated note containing links to other notes about a topic. Links over folders. Hierarchical MOCs (Domain MOC → Topic MOC → Concept notes). Hand-curated navigation. MoC of MoCs at the root.

**Decision criteria — use when:**
- The system is Obsidian or another wikilink-based tool
- There are 5-10+ notes that naturally group around a topic
- Multiple navigation paths to the same content are needed
- The user wants hand-curated entry points (not just folder browsing)
- Cross-cutting concerns don't fit a single hierarchy

**Role in a combination:** Provides the navigation layer. Works with any folder structure — MOCs sit on top and provide curated access paths. Each project, domain, or entity gets its own MOC.

**Strengths:** Perfect for Obsidian's wikilink architecture; allows multiple organizational views simultaneously; hand-curation adds context; scales well; can combine with Dataview for dynamic MOCs.
**Weaknesses:** Requires manual curation; no enforcement; can become inconsistent if not maintained.

---

## 7. Domain-Driven Design (DDD) for Documentation

**Origin:** Eric Evans, "Domain-Driven Design" (2003). Adapted for knowledge organization.

**Principle:** Bounded Contexts (explicit boundaries where terms and rules apply consistently). Ubiquitous Language within each context. Context Mapping (Partnership, Customer-Supplier, Conformist, Anti-Corruption Layer). Strategic Design.

**Decision criteria — use when:**
- The vault contains multiple distinct entities (companies, teams, brands, domains)
- Each entity has its own terminology that may conflict with others
- Shared resources (databases, servers, APIs) serve multiple entities
- There are translation boundaries between areas (same term, different meaning)

**Role in a combination:** Provides the primary top-level structure. Each entity is a bounded context with its own folder, MOC, and ubiquitous language. Shared resources get their own context with explicit relationships mapped.

**Strengths:** Excellent for multi-entity vaults; each entity has consistent terminology; shared resources get explicit relationships; prevents terminological confusion.
**Weaknesses:** Designed for software architecture, not documentation; requires upfront domain modeling; overkill for single-entity vaults.

---

## 8. Bowker and Star — "Sorting Things Out"

**Origin:** Geoffrey C. Bowker and Susan Leigh Star, MIT Press 1999.

**Principle:** Classification is not neutral — it embeds values and power structures. Boundary objects inhabit multiple social worlds. Infrastructure is classification. Invisible labor maintains classification systems.

**Decision criteria — use when:**
- As a critical lens alongside any structural methodology
- The vault serves multiple stakeholders with different needs
- There are items that "don't fit" any category — these are signals, not errors
- Classification decisions have social or political implications

**Role in a combination:** Critical overlay. Does not provide structure — provides awareness. Use it to question whether the chosen structure serves all users or only the dominant one.

**Strengths:** Prevents rigid universal classifications; validates boundary objects; warns about blind spots.
**Weaknesses:** Theoretical and critical, not prescriptive; does not provide implementation guidance.

---

## 9. Polyhierarchical Faceted Classification

**Origin:** Library and information science, based on Ranganathan's faceted classification. Implemented in Getty AAT, museum-digital. SKOS standard.

**Principle:** Polyhierarchy (terms can have multiple parent categories). Facets (multiple independent taxonomies along different dimensions). All-Some Rule. SKOS standard for knowledge organization systems.

**Decision criteria — use when:**
- Items genuinely belong to multiple categories simultaneously
- Cross-entity resources need to be findable from multiple entry points
- A tag system or frontmatter metadata is available (polyhierarchy is hard in pure folders)
- The vault has or needs a tag taxonomy

**Role in a combination:** Provides the tagging/metadata layer. Folders give each item one home; tags provide multiple access paths. Usually implemented as `empresa/x`, `tipo/y`, `status/z` nested tags in Obsidian.

**Strengths:** Reflects real-world complexity; multiple access paths without duplication; well-established in library/museum practice.
**Weaknesses:** Complex to implement in file systems (requires metadata); can become unwieldy if overused; requires tag maintenance.

---

## 10. Every Folder is a Project

**Origin:** Monorepo practices (Nx, Turborepo). R-That Wiki "Folder-as-project" pattern.

**Principle:** Folder as source of truth — project identity is determined by directory location, not metadata. No `project` field in frontmatter (derived from path). Atomic operations — moving a project is one command. Collocation — things that change together live together.

**Decision criteria — use when:**
- The vault contains multiple projects that should be atomic units
- Projects are currently scattered across multiple directories
- Project components (web, API, mobile, docs) should be collocated
- Moving or archiving a project should be a single operation

**Role in a combination:** Provides the project-level folder structure. Each project is a self-contained folder with all its components. Pairs with DDD for the entity level above projects.

**Strengths:** Simple and unambiguous; atomic operations; clear ownership boundaries; works well with version control; scales to hundreds of projects.
**Weaknesses:** Single location per project (no polyhierarchy); cross-project resources need separate structure; can lead to deep nesting if not balanced.

---

## Common combinations

| Vault type | Methodologies | Why |
|---|---|---|
| Multi-company project vault | DDD + Every Folder is a Project + MOC + Polyhierarchical Tags | DDD for entity boundaries, Every Folder for project atomicity, MOC for navigation, Tags for multi-categorization |
| Personal knowledge base | Zettelkasten + MOC | Zettelkasten for linking philosophy, MOC for curated entry points |
| Software documentation | IA (faceted) + Every Folder is a Project | IA for multi-dimensional access, Every Folder for project collocation |
| Research notebook | Zettelkasten + IA + TRUST/FAIR | Zettelkasten for connections, IA for facets, TRUST for preservation |
| Small project vault (< 50 files) | Johnny.Decimal + MOC | Johnny.Decimal for discipline, MOC for navigation |
| Archive-heavy vault | OAIS + DDD + MOC | OAIS for archival, DDD for entity boundaries, MOC for active content navigation |
