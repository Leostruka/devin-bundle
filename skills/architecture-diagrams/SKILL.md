---
name: architecture-diagrams
description: Use when the deliverable is a physical diagram artifact (.svg/.png) — C4 models, dense class diagrams, network topology rendered via PlantUML. Not for diagrams embedded in Markdown (use Mermaid there).
argument-hint: What architecture should I diagram?
triggers: [user]
---

# Architecture Diagrams (PlantUML)

Generates physical diagram artifacts via the public PlantUML server —
no Java required. Renders C4 models, dense class diagrams, and network
topologies that Mermaid cannot express well.

## Tool boundary — Mermaid vs PlantUML

**Mermaid** for diagrams *embedded in Markdown* — sequence, flow, state,
gitgraph, mindmap, ER — quick logic inside docs, wikis (`obsidian-workflow`),
and reports. Validated inline by the `validate-mermaid` hook.

**PlantUML** *exclusively* for *physical artifacts* (`.svg`/`.png` files):

- C4 models (Context / Container / Component / Deployment)
- Dense class diagrams (many entities, relations, generics)
- Network / deployment topology

If the user wants a diagram inside a Markdown doc → Mermaid. If they want a
file they can open, print, or attach → PlantUML via this skill.

## Where it is

- Renderer: `extensions/diagram-tools/plantuml_renderer.py` (installed at
  `%APPDATA%\devin\extensions\diagram-tools\`) — stdlib-only; Deflate +
  PlantUML modified-Base64 + GET to `plantuml.com/plantuml/{svg,png}/`.

## Flow

1. Write the PlantUML source to a file (e.g. `.devin/scratch/diagram.puml`
   or a path the user chooses). Never render from a heredoc — keep the
   source file as the editable artifact.
2. **Syntax sanity before the network** (mandatory):

   ```bash
   python extensions/diagram-tools/plantuml_renderer.py --check diagram.puml
   ```

   Fix all reported errors before proceeding.
3. Render:

   ```bash
   python extensions/diagram-tools/plantuml_renderer.py diagram.puml            # .svg
   python extensions/diagram-tools/plantuml_renderer.py diagram.puml --format png
   ```

   Verify `ok: true` in the JSON output, then open the artifact for the user.
4. If the server returns a syntax-error image (non-SVG body), read the error
   it reports, fix the source, re-check, re-render.

## C4 model rules

Use the C4-PlantUML stdlib — always remote-include, never vendor:

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

Person(user, "User", "End user")
System_Boundary(sys, "System") {
  Container(app, "App", "Python", "Does X")
  ContainerDb(db, "DB", "SQLite", "Stores Y")
}
Rel(user, app, "Uses")
Rel(app, db, "Reads/Writes")
@enduml
```

- Layer `!include` by depth: `C4_Context.puml` ⊂ `C4_Container.puml` ⊂
  `C4_Component.puml`; `C4_Deployment.puml` for topology.
- One diagram per abstraction level — do not mix Context and Component.
- Every element gets `alias`, `label`, `technology`, `description` (4 args).
- `Rel(a, b, "verb")` for every arrow; direction = call order.
- Keep aliases stable across levels so diagrams stay cross-referenceable.

## Gotchas

- The public server requires network — if offline, say so and keep the
  `.puml` source; it renders later unchanged.
- Server-side syntax errors return an image *containing* the error —
  the script detects this and exits non-zero. Treat it as a fix-and-retry.
- PlantUML is whitespace/keyword-sensitive: `@enduml` (not `@end uml`),
  arrows are `-->` / `..>` not `->`.
- Large C4 models hit URL limits (~8KB encoded); split into per-level files.
