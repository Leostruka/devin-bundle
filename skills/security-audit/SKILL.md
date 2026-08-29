---
name: security-audit
description: "Use when the user wants to audit code, dependencies, or infrastructure for security issues. Covers SAST, dependency scanning, secret leak detection, and OWASP-style checks."
triggers: [user, model]
---

# Security Audit

Defensive security analysis of code, dependencies, and configuration.

## When to use

- User asks for a security review or audit.
- Adding untrusted dependencies or new secrets handling.
- Before exposing a service to the internet.
- After a security incident or alert.

## Core protocol

1. **Scope the surface.** Identify code paths, inputs, auth, secrets, and network boundaries.
2. **Run static analysis.** Use project linters and SAST tools if available.
3. **Check dependencies.** Look for known CVEs, outdated packages, suspicious licenses.
4. **Hunt for secrets.** Run secret-scanning tools or grep for high-risk patterns.
5. **Review auth and input.** Verify auth checks, input validation, output encoding, and least privilege.
6. **Document findings.** Rank by severity; do not exploit, only detect.

## See also

- `code-review` — general code review before merge.
- `security-audit` — defensive security-specific review.

## Output rule

- Produce a findings list: severity, file, issue, recommendation, and verification command.
- Never expose real credentials or attack a live system.
