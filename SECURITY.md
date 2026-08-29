# Security Policy

## Devin CLI is Not a Security Sandbox

The Devin CLI agent executes commands, writes files, and runs code with the
user's full OS permissions. There is no isolation layer between the agent and
the system. This is documented in Rule 13 of `AGENTS.md`.

## Reporting a Vulnerability

If you discover a security vulnerability in this bundle (skills, hooks,
scripts, or config that could be exploited):

1. **Do NOT open a public issue.**
2. Email the repository owner directly.
3. Include: description, reproduction steps, potential impact.
4. You will receive a response within 72 hours.

## Security Guardrails in This Bundle

| Guardrail | Mechanism | Scope |
|---|---|---|
| AI signature blocking | `check-ai-signature.py` hook | PreToolUse (exec/write/edit) + Stop |
| Push-without-green blocking | `check-push-green.py` hook | PreToolUse (exec) |
| Post-compaction re-priming | `constraint-pinning.py` hook | PostCompaction |
| Refinement review prompt | `refine-review-prompt.py` hook | Stop |
| Reward hacking guard | `primeagent-reference` Refine mode guardrails | Self-improvement loops |
| Untrusted code warning | Rule 13 in AGENTS.md | All sessions |

## What This Bundle Does NOT Protect Against

- **Malicious skills:** a skill is a set of instructions the agent follows. Read any SKILL.md before invoking it on a real task.
- **Malicious MCP servers:** MCP servers gain tool access. Review their code, permissions, and network behavior before adding to `mcp_config.json`.
- **Untrusted code execution:** the agent runs code with your permissions. Run untrusted code in an external sandbox (container, VM, restricted user).
- **Secret leakage:** secrets are masked in export by default. Never use `-NoMask` with `-Push` on a public repo.

## Secret Handling

| File | Default export | With `-NoMask` |
|---|---|---|
| `config.json` | `org_id` → MASKED | real org_id |
| `mcp_config.json` | env values → MASKED | real tokens |
| `credentials.toml` | ALL values → MASKED | real API keys |

**Never commit unmasked secrets.** Use `-NoMask` only for local backup or
direct transfer between trusted machines.
