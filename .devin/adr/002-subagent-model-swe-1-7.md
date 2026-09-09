# ADR 002: Subagent model `swe-1-7`

## Status

Accepted

## Context

The bundle provides specialized subagent profiles (`architect`, `debugger`,
`implementer`, `qa-ci`, `researcher`, `reviewer`). These agents run
independent, often bounded tasks. `glm-5-2` is the default free parent model,
but the bundle can route subagents to a stronger coding model.

## Decision

Use `swe-1-7` as the dedicated model for custom subagent profiles. `glm-5-2`
remains the parent model for cost control. The model is declared in
`agent.model` in `config.json` for the parent and in each `agents/*.md` profile
for subagents.

## Consequences

- Subagent tasks get stronger reasoning for code, debugging, and verification.
- The parent remains cheap for routing and light edits.
- Users can override the model locally without changing the bundle.
