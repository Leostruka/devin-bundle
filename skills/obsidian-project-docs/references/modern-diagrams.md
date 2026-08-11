# Modern diagram types for Obsidian Canvas

This reference maps modern diagram approaches to JSON Canvas files inside the Obsidian vault. The goal is to reduce abstraction by giving each stakeholder the right zoom level.

## Why not UML?

UML is comprehensive but heavy. Most engineering teams use only a subset. Modern alternatives are lean, zoomable, and fit the "boxes and lines" style that Obsidian Canvas renders well.

| Modern approach | Replaces / complements UML | Best for | Obsidian Canvas file |
|-----------------|----------------------------|----------|----------------------|
| **C4 model** | Package, component, deployment, use-case diagrams | Communicating architecture at 4 zoom levels | `Diagrams/Context.canvas`, `Container.canvas`, `Component.canvas` |
| **Domain / DDD context map** | UML class diagram (domain view) | Bounded contexts, teams, upstream/downstream | `Diagrams/Domain.canvas` |
| **Event storming / flow** | Activity, sequence, state diagrams | Business / data flow over time | `Diagrams/Flow.canvas` |
| **Data model** | ER / class diagram | Tables, entities, relationships | `Diagrams/DataModel.canvas` |
| **State / lifecycle** | State machine diagram | Entity states and transitions | `Diagrams/State.canvas` |

## C4 model on Canvas

The C4 model has four static levels. Each is a separate `.canvas` file.

### Level 1 — System Context

- **Person** (users/actors): purple `6`
- **System** (in scope): green `4`
- **External system**: orange `2`
- **Relationship arrows**: labelled edges

Zoom: highest. Audience: non-technical stakeholders.

### Level 2 — Container

Containers are separately deployable / runnable units:

- Web app
- API / service
- Database
- Message queue
- File store
- Mobile app

Colors:

- Web / mobile app: `4` green
- API / service: `5` cyan
- Database: `3` yellow
- Queue / broker: `2` orange
- External: `1` red

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

Optional. Usually use the IDE or generated class diagrams. In Canvas this can be a small group with key classes and inheritance/composition edges.

## DDD context map

Use `Diagrams/Domain.canvas` for bounded contexts:

- Bounded contexts as colored group nodes
- Domain events as small text nodes
- Arrows labelled with:
  - `upstream` / `downstream`
  - `partnership`
  - `shared kernel`
  - `customer-supplier`
  - `conformist`
  - `anti-corruption layer`

## Event / data flow

- Start with a trigger node
- Flow left-to-right or top-to-bottom
- Use edges with labels like `emits`, `reads`, `writes`, `calls`, `returns`
- Group swim-lanes by module or actor

## Data model canvas

- Entity / table as text or group node
- Columns listed inside the text
- Relationships as edges with cardinality labels: `1`, `0..1`, `*`, `1..*`
- Distinguish strong/weak, identifying/non-identifying relationships by edge style

## State / lifecycle canvas

- States as rounded-ish text nodes (or just text nodes)
- Transitions as directed edges with trigger / guard labels
- Initial state in green, terminal in red, intermediate in blue

## Canvas conventions for this project

- Align nodes to a 20 px grid.
- Keep edges short and orthogonal when possible.
- Group nodes by concern (domain, layer, system).
- Use colors consistently across all diagrams.
- Add a legend text node in the corner of every diagram.

## When to create / update diagrams

- At project start: Context and Container diagrams.
- When adding a domain or bounded context: Domain canvas.
- When adding / changing a module: Component diagram.
- When adding / changing a data model: Data model canvas.
- When defining a workflow or state machine: Flow / State canvas.

## Linking diagrams to notes

Every diagram should have a companion note:

- `Diagrams/Context.canvas` ↔ `01-Architecture.md`
- `Diagrams/DataModel.canvas` ↔ `02-Database.md`
- `Diagrams/Domain.canvas` ↔ `07-Glossary.md`
- `Diagrams/Component.canvas` ↔ `Modules/<Module>.md`

Use Obsidian file cards (`type: "file"`) to embed the note inside the canvas when useful.
