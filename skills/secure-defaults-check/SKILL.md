---
name: secure-defaults-check
description: Use when checking that a project or change follows secure defaults before committing or deploying.
---

# Secure Defaults Check

Automated checklist for secure defaults. Catches common security mistakes before they reach production.

## When to use

- Before committing code that touches secrets, endpoints, or infrastructure.
- Before deploying to production.
- When setting up a new project.
- When the user asks for a security check.

## Checklist

| Check | What to verify |
|-------|----------------|
| `.env` in `.gitignore` | Secrets are not committed. |
| `.env.example` exists | Template for required env vars. |
| No hardcoded secrets | No API keys, passwords, or tokens in code. |
| No public S3/URLs | Storage and endpoints are not publicly accessible. |
| No unauthenticated endpoints | All endpoints require auth or have a documented exception. |
| Destructive actions confirmed | `DELETE`, `DROP`, `TRUNCATE` require explicit confirmation. |
| Passwords hashed | No plaintext passwords; use standard hashing (bcrypt, argon2). |
| No custom crypto | Use standard libraries, not homemade encryption. |
| Dependencies updated | No known vulnerable dependencies. |
| Logs sanitized | No secrets or PII in logs. |

## Process

```
Before commit/deploy
  → Run secure-defaults-check
  → If any check fails: fix or document exception
  → If all pass: proceed
```

## Example

```bash
# Check for hardcoded secrets
grep -r "api_key\|password\|secret" --include="*.py" --include="*.ts" .

# Check .gitignore
grep -q "^\.env$" .gitignore || echo "FAIL: .env not in .gitignore"

# Check for public S3 URLs
grep -r "s3\.amazonaws\.com" --include="*.py" --include="*.ts" .
```

## Anti-patterns

- Committing `.env` or secrets.
- Creating public endpoints without auth.
- Using custom crypto or plaintext passwords.
- Skipping confirmation for destructive actions.
- Logging secrets or PII.

## Cross-skills

- `security-audit` — deeper review after this check passes.
- `verification-before-completion` — use as final gate before claiming done.
- `project-setup` — includes this check in new project scaffolding.
