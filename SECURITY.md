# Security Policy

## Devin CLI is Not a Security Sandbox

The agent executes commands, writes files, and runs code with the user's full OS
permissions. No isolation layer. Documented in Rule 13 of [AGENTS.md](AGENTS.md).

## Reporting a Vulnerability

If you discover a security vulnerability in this bundle (skills, hooks, scripts, or config):

1. **Do NOT open a public issue.**
2. Email the repository owner directly.
3. Include: description, reproduction steps, potential impact.
4. Response within 72 hours.

## Guardrails

Guardrails are enforced by scripts in `scripts/` and configured in `hooks.v1.json`.
Read those files for the authoritative list and mechanism. Summary:

- AI signature blocking (`check-ai-signature.py`)
- Push-without-green blocking (`check-push-green.py`)
- Constraint pinning after compaction (`constraint-pinning.py`)
- Refinement review prompt (`refine-review-prompt.py`)
- Reward hacking guard (Rule 16 + `refine` skill guardrails)
- Untrusted code warning (Rule 13)

## Secret Handling

Secrets are masked in export by default. For per-file masking rules, read
`export.ps1` / `export.sh`. **Never commit unmasked secrets.** Use `-NoMask`
only for local backup or direct transfer between trusted machines.
