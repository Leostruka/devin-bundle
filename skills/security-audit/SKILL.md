---
name: security-audit
description: Use when the user wants to audit code, dependencies, or infrastructure for security issues. Covers SAST, dependency scanning, secret leak detection, and OWASP-style checks.
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

## Checklist — 5 security principles

Apply this checklist to every audit. Each item comes from the `sec-needs` source.

| Principle | What to verify | What to flag |
|---|---|---|
| **1. Minimize attack surface** | Every line of code, every input, every endpoint, every service, every log line is a possible vector. | Unnecessary code, unauthenticated endpoints, public S3/storage URLs, sequential IDs on resource reads, sensitive data in logs, timing leaks in comparisons. |
| **2. Least privilege** | Services, users, and DB access have only the permissions they need. | Over-privileged service accounts, broad IAM policies, DB access from outside the VPC, frontend code calling the DB directly, hardcoded credentials. |
| **3. Secure defaults** | The default state is safe: hidden passwords with opt-in reveal, confirmation for destructive actions, MFA required, new accounts must change default password. | Default-visible passwords, destructive actions without confirmation, missing MFA prompts, insecure default credentials. |
| **4. Standard crypto** | Sensitive data is encrypted with standard algorithms; no home-grown crypto. | Plain-text passwords, custom hash functions, missing `bcrypt`/`argon2`, unencrypted sensitive payloads. |
| **5. Updates and monitoring** | Dependencies are patched promptly; SAST and WAF are in place. | Outdated dependencies with CVEs, missing Dependabot/renovate, missing SAST/WAF coverage. |

## See also

- `code-review` — general code review before merge.
- `security-audit` — defensive security-specific review.

## Output rule

- Produce a findings list: severity, file, issue, recommendation, and verification command.
- Never expose real credentials or attack a live system.
