# Role matrix

Maps project scope to the roles required. Saved as `.devin/role-matrix.md`.
A new `workers/<role>/` exists only when this matrix shows a gap no existing
role covers.

## Matrix

| Scope area | Role needed | Existing profile? | Action | Justification |
|---|---|---|---|---|
| example: external API research | researcher | yes (`agents/researcher.md`) | reuse | |
| example: UX audit | ux-auditor | no | spawn workers/ux-auditor | gap: no design-judgment role |

## Spawn checklist (per new role)

- [ ] `workers/<role>/role.md` charter filled (see `worker-role.md`)
- [ ] `workers/<role>/.devin/notes/` + `.devin/adr/` created
- [ ] gap justification recorded in the matrix row
- [ ] base profile chosen (`implementer` / `subagent_general` / etc.)

## Anti-pattern

Do not spawn roles for variety. One role covers a scope area unless two
scope areas would otherwise share a writer on the same files.
