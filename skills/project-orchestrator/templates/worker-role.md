# Worker role charter

Saved as `workers/<role>/role.md` in the target project when the role
matrix spawns or activates a role. The role's accumulated knowledge lives in
`workers/<role>/.devin/` (`notes/` for domain knowledge, `adr/` for
role-local decisions), separate from the project-level `.devin/`.

```markdown
# Role: <name>

## Mandate

<what this role owns end to end>

## Boundaries

- Owns: <files/areas>
- Reads but does not write: <files/areas>
- Never touches: <files/areas>

## Base profile

<bundle profile used for dispatches: implementer / researcher / ...>

## Definition of done

- <what a completed delegation looks like>
- handoff-doc written to `.devin/handoffs/`

## Standing context

- key artifacts: <paths the role always re-reads>
- knowledge base: `workers/<role>/.devin/notes/`
- role ADRs: `workers/<role>/.devin/adr/`
```
