# ADR 002: Subagent model family

## Status

Superseded (2026-10-31) by the SWE-2 family routing in
`data/bundle-models.json`. See `.devin/docs/MODEL-GUIDE.md` and
`.devin/docs/DEVIN-CLI-COMPATIBILITY.md` (`agent.subagent_model`).

Original decision: pin `swe-1-7` for custom subagent profiles with `glm-5-2`
as the free parent. Both model identifiers were retired by the SWE-2
migration (`swe-2-high` parent, `swe-2-max`/`swe-2-medium` subagents).

## Context (historical)

The bundle provides specialized subagent profiles (`architect`, `debugger`,
`implementer`, `qa-ci`, `researcher`, `reviewer`). These agents run
independent, often bounded tasks. The default free parent model handles
routing; subagents can be routed to a stronger coding model.

## Current decision

Subagent profiles pin `swe-2-max` (judgment/planning) or `swe-2-medium`
(bounded execution) per `data/bundle-models.json`; the parent runs
`swe-2-high`. `agent.subagent_model` in `config.json` pins the fallback for
`subagent_explore` and unpinned custom agents (ships `swe-2-max`).

## Consequences

- Model identities follow `data/bundle-models.json`, not this ADR; update
  the registry and agent `model:` pins when the family changes.
- Free-tier policy (parent free => subagents free) is documented in
  MODEL-GUIDE.md, not here.
