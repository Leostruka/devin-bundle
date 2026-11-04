# ADR 007: File-based issue tracker under .devin/scratch

## Status

Accepted

## Context

Bundle work is driven by agents. Agents need issues they can read,
claim, and resolve with plain file tools, offline, inside the repo they
are modifying. GitHub Issues requires network, auth, and a tool surface
(`gh`) that agents may not have, and cannot be diffed in a PR alongside
the code it describes.

## Decision

Work items live as Markdown under `.devin/scratch/<effort>/issues/NN-slug.md`
with `spec.md` and `map.md` per effort; the `issue-tracker` agent
profile (`.devin/agents/issue-tracker.md`) defines conventions
(numbering, `Status:`, `## Answer` on resolve). `.devin/issues/` keeps
its separate role: milestone- and design-level issues (`ISSUE_*`,
`MILESTONE_*`) that are not scoped to a single work effort. GitHub
Issues remains the human-facing intake for external reports; PR numbers
in CHANGELOG refer to the GitHub surface.

## Consequences

- Issue state is diffable, reviewable, and travels with clones; an agent
  resolves an issue in the same commit as the fix.
- Numbering is local to each effort; no global uniqueness.
- Accepted costs: no notifications, no assignee field, no cross-clone
  dedup, and no automatic linkage to PRs (references are by convention,
  e.g. commit messages and `## Answer` text).
- Two in-repo trackers coexist by scope: scratch = per-effort work
  items, `.devin/issues/` = milestone/design backlog. If that split
  blurs, `.devin/issues/` should be folded into scratch efforts or
  deprecated explicitly.
