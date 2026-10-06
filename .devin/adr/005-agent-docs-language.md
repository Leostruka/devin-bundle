# ADR 005 - Distributed agent-facing docs are English

- Status: accepted (user decision, 2026-10-05 intake follow-up)
- Date: 2026-10-05
- Track: agent-docs-rag

## Context

`.devin/docs/` mixes pt-BR (SKILL-TIERS, MODEL-GUIDE, TOOLS-MAP,
3D-STACK-INSTALL) and EN. The bundle distributes these files into every
consumer's Devin home; vision NFR-4 requires English for distributed
artifacts.

## Decision

Distributed docs under `.devin/docs/` are English. The four pt-BR files are
translated; `3D-STACK-INSTALL.md` is also genericized (machine-specific
paths removed) since it ships to every install. Maintainer-local material
under `.devin/` that is not installed (plans, ledgers, notes, research)
keeps the author's language. README/CHANGELOG stay as-is this track (their
pt-BR is human-facing; flagged Low, deferred).

## Consequences

- Slices rewriting SKILL-TIERS/TOOLS-MAP write the new text in English
  directly; no separate translate-then-edit pass.
- New distributed docs must be English at creation.
