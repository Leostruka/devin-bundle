---
name: security
description: Use when auditing code, dependencies, or infrastructure for security issues (SAST, dependency scanning, secret leak detection, OWASP-style checks), or when checking that a project or change follows secure defaults before committing or deploying.
triggers: [user, model]
---

# Security

Two layers: **secure-defaults check** (fast pre-commit/deploy gate) and
**security audit** (deeper defensive review). Defensive only — detect and
report, never exploit.

## Secure-defaults checklist (gate before commit/deploy)

| Check | Verify |
|---|---|
| `.env` in `.gitignore` | Secrets not committed |
| `.env.example` exists | Template for required vars |
| No hardcoded secrets | No keys/passwords/tokens in code |
| No public S3/URLs | Storage + endpoints not public |
| No unauthenticated endpoints | Auth required or documented exception |
| Destructive actions confirmed | DELETE/DROP/TRUNCATE need confirmation |
| Passwords hashed | bcrypt/argon2, never plaintext |
| No custom crypto | Standard libraries only |
| Dependencies updated | No known-vulnerable deps |
| Logs sanitized | No secrets/PII in logs |

Quick greps:

```bash
grep -r "api_key\|password\|secret" --include="*.py" --include="*.ts" .
grep -q "^\.env$" .gitignore || echo "FAIL: .env not in .gitignore"
grep -r "s3\.amazonaws\.com" --include="*.py" --include="*.ts" .
```

Helper: `python3 scripts/check.py` (this skill's `scripts/`). Any failure →
fix or document the exception before proceeding.

## Security audit (deeper)

1. **Scope the surface** — code paths, inputs, auth, secrets, network boundaries.
2. **Static analysis** — project linters/SAST if available.
3. **Dependencies** — CVEs, outdated packages, suspicious licenses.
4. **Hunt secrets** — scanning tools or high-risk greps.
5. **Auth + input** — auth checks, validation, output encoding, least privilege.
6. **Document** — findings ranked by severity. Detect only.

### Five security principles

| Principle | Flag |
|---|---|
| **Minimize attack surface** | Unnecessary code, unauthenticated endpoints, public storage, sequential IDs on reads, secrets in logs, timing leaks |
| **Least privilege** | Over-privileged service accounts, broad IAM, DB access outside VPC, frontend→DB direct, hardcoded creds |
| **Secure defaults** | Visible passwords, unconfirmed destructive actions, missing MFA, default creds |
| **Standard crypto** | Plaintext passwords, custom hashing, missing bcrypt/argon2 |
| **Updates + monitoring** | Vulnerable deps, missing Dependabot/SAST/WAF |

## Output rule

Findings list: severity, file, issue, recommendation, verification command.
Never expose real credentials or attack a live system.
