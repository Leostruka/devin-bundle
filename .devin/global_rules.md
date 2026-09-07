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

## Security and project hygiene

- Never output or log secrets, API keys, passwords, tokens, or private keys.
- Never commit secrets to the repository. If a secret is exposed, warn and ask for rotation.
- Treat user input as untrusted; validate and sanitize before use.
- Default to private endpoints, private S3/storage URLs, and least privilege. Public endpoints or URLs require documented justification.
- Use secure defaults: confirmation for destructive actions, hidden credentials with opt-in reveal, multi-factor auth where applicable.
- Keep the database and internal services inside private networks/VPCs; don't expose credentials to frontend code.
- Don't delete tests without explicit approval.
- Prefer the smallest solution that works; reject overengineering and token maxing.
- Declare intent, user impact, and boundaries before coding.
