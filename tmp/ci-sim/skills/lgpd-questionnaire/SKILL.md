---
name: lgpd-questionnaire
description: Use when the user asks for an LGPD/data-protection compliance review of an app or service - data inventory, legal basis, third-party sharing, subject rights, breach response. Produces an evidence-cited compliance matrix, not legal advice.
triggers: [user, model]
---

# LGPD Compliance Questionnaire

Skeleton - expand question groups into a full bank during implementation.

## When to use

- User asks for an LGPD, privacy, or data-protection audit.
- Pre-launch review (app store registration, new market).
- Adding a third-party SDK or new data flow.
- Responding to a data-subject complaint or ANPD inquiry.

Do NOT use for pure vulnerability hunting - route to `security-audit` or
`security-audit-cf`.

## Inputs

- `jurisdiction` - default `LGPD`; `GDPR`/`CCPA` reuse the same groups
  with swapped references and deadlines.
- `surface` - mobile, web, backend, or mixed; controls which manifest
  and permission sources are scanned.
- `scope` - optional paths (AndroidManifest, package.json, logging dir)
  to bound the scan.

## Questionnaire groups

1. **Data inventory and legal basis** - what personal data, where stored,
   which Art. 7/11 basis, sensitive-data handling.
2. **Permissions vs need** - each requested permission justified by a
   feature; flag mandatory-without-need.
3. **Third-party sharing register** - every external service listed with
   what data leaves and under which safeguard.
4. **Retention and minimization** - retention windows, deletion paths,
   over-collection flags.
5. **Subject rights** - access/correction/deletion channel; 15-day
   response SLA verifiable in the flow.
6. **Logging and masking** - no complete personal data in logs; masking
   verified at call sites.
7. **Consent and UX confirmations** - granular consent records;
   double-confirmation on payment/destructive actions (aligns with
   `secure-defaults-check`).
8. **Breach response** - incident runbook, ANPD notification within the
   legal window (Art. 48), communication plan to affected subjects.

## Evidence rules

- Every answered item cites `file:line` or a config artifact.
- Unverifiable items are marked `needs-owner` - never answered by
  guessing.
- Absence of evidence is a finding, not a pass.

## Output

Markdown matrix:

| # | Question | Status | Evidence | Gap | Remediation |
|---|----------|--------|----------|-----|-------------|

Status values: `compliant`, `partial`, `gap`, `needs-owner`.
Rank gaps by severity like `security-audit` findings.

## Boundaries

- Working draft for DPO/legal review - not legal advice.
- Read-only: reports, never modifies code or config.
- Jurisdiction-specific contacts (DPO, ANPD) live in project context,
  not in this skill.

## See also

- `security-audit` - vulnerability and attack-surface review.
- `secure-defaults-check` - confirmation/credential UX checklist.
