# Modern diagram types for Mermaid

This reference maps modern diagram approaches to Mermaid diagrams inside the Obsidian vault. The goal is to reduce abstraction by giving each stakeholder the right zoom level.

## Why not UML?

UML is comprehensive but heavy. Most engineering teams use only a subset. Modern alternatives are lean, zoomable, and fit the "boxes and lines" style that Mermaid renders well.

| Modern approach | Replaces / complements UML | Best for | Mermaid diagram |
|-----------------|----------------------------|----------|-----------------|
| **C4 model** | Package, component, deployment, use-case diagrams | Communicating architecture at 4 zoom levels | `Diagrams/Context.md`, `Container.md`, `Component.md` |
| **Domain / DDD context map** | UML class diagram (domain view) | Bounded contexts, teams, upstream/downstream | `Diagrams/Domain.md` |
| **Event storming / flow** | Activity, sequence, state diagrams | Business / data flow over time | `Diagrams/Flow.md` |
| **Data model** | ER / class diagram | Tables, entities, relationships | `Diagrams/DataModel.md` |
| **State / lifecycle** | State machine diagram | Entity states and transitions | `Diagrams/State.md` |

## C4 model in Mermaid

The C4 model has four static levels. Each is a separate Mermaid diagram.

### Level 1 — System Context

- **Person** (users/actors): `User([User])` rounded shape
- **System** (in scope): `System[MyApp]` square
- **External system**: `Email[Email Service]` square
- **Relationship arrows**: labelled edges (`System --> Email : sends`)

Zoom: highest. Audience: non-technical stakeholders.

### Level 2 — Container

Containers are separately deployable / runnable units:

- Web app
- API / service
- Database
- Message queue
- File store
- Mobile app

Node styling conventions:

- Web / mobile app: green
- API / service: cyan
- Database: yellow
- Queue / broker: orange
- External: red

Zoom: high. Audience: technical but cross-functional.

### Level 3 — Component

Components live inside a container:

- Controllers
- Services
- Repositories
- Gateways
- Use cases / interactors

Colors per type or sub-system.

Zoom: medium. Audience: the team owning the container.

### Level 4 — Code

Optional. Usually use the IDE or generated class diagrams. In Mermaid this can be a small `classDiagram` with key classes and inheritance/composition edges.

## DDD context map

Use `Diagrams/Domain.md` for bounded contexts:

- Bounded contexts as `subgraph` blocks
- Domain events as small nodes
- Arrows labelled with:
  - `upstream` / `downstream`
  - `partnership`
  - `shared kernel`
  - `customer-supplier`
  - `conformist`
  - `anti-corruption layer`

## Event / data flow

- Start with a trigger node
- Flow left-to-right (`graph LR`) or top-to-bottom (`graph TB`)
- Use edges with labels like `emits`, `reads`, `writes`, `calls`, `returns`
- Group swim-lanes by module or actor using `subgraph`

## Data model diagram

- Use `erDiagram` syntax
- Entities with columns listed inside `{ }`
- Relationships as edges with cardinality labels: `||--o{`, `||--|{`, `}o--o{`
- Distinguish strong/weak, identifying/non-identifying relationships by edge style

## State / lifecycle diagram

- Use `stateDiagram-v2` syntax
- States as nodes
- Transitions as directed edges with trigger / guard labels
- Initial state `[*]` in green, terminal `[*]` in red, intermediate in blue

## Mermaid conventions for this project

- Use `graph TB` or `graph LR` for flow diagrams
- Label every edge with the relationship and technology
- Add a legend comment block at the top of the diagram
- Use consistent node shapes: `([ ])` for actors, `[ ]` for systems, `[( )]` for databases
- Include a `<!-- Sources: ... -->` comment block listing source files

## When to create / update diagrams

- At project start: Context and Container diagrams.
- When adding a domain or bounded context: Domain diagram.
- When adding / changing a module: Component diagram.
- When adding / changing a data model: Data model diagram.
- When defining a workflow or state machine: Flow / State diagram.

## Linking diagrams to notes

Every diagram should have a companion note:

- `Diagrams/Context.md` ↔ `02-Architecture.md`
- `Diagrams/DataModel.md` ↔ `03-Database.md`
- `Diagrams/Domain.md` ↔ `08-Glossary.md`
- `Diagrams/Component.md` ↔ `Modules/<Module>.md`

Use wikilinks (`[[...]]`) in the `## Links` section of each diagram to connect back to the relevant note.
