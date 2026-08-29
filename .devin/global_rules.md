# Project rules

## Project context

Read `.devin/CONTEXT.md` before changing bundle behavior, declarations, installation, export, hooks, or skills.

Treat root files as distribution artifacts. Keep project-specific agent context under `.devin/`.

## Agent skills

### Issue tracker

Issues live as Markdown under `.devin/scratch/`. See `.devin/agents/issue-tracker.md`.

### Triage labels

Use the canonical local status vocabulary. See `.devin/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `.devin/agents/domain.md`.

## Verification

Run `python audit.py` and `python -m pytest` before committing.

Run the platform exporter in dry-run mode when changing exported bundle resources.
