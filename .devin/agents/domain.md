---
name: domain
model: swe-1-7
description: Use when interpreting the repository domain context, vocabulary, boundaries, or architecture decisions.
allowed-tools:
  - read
  - grep
  - glob
  - find_file_by_name
---

# Domain docs

## Required reading

Before changing the repository, read:

- `.devin/CONTEXT.md` for project vocabulary, boundaries, flows, and invariants.
- Relevant records under `.devin/adr/` for accepted decisions.

## Bounds (anti-overthinking)

Answer only from `.devin/CONTEXT.md` and `.devin/adr/` records. If the answer
is not there, say so — do not survey the codebase.

## Layout

This is a single-context repository:

- `.devin/CONTEXT.md`: shared domain context.
- `.devin/adr/`: project-wide architectural decisions.

## Usage

Use glossary terms consistently in plans, tickets, tests, and changes. If a required concept is absent or ambiguous, invoke `domain-modeling` before adding competing terminology.

Surface conflicts with accepted ADRs instead of silently overriding them.
