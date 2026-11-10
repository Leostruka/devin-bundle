# Eval: LGPD / compliance questionnaire skill (issue #448, R7-15)

Scope decision: does a reusable LGPD compliance questionnaire belong in the
bundle (`skills/`) or stay user-side (per-project prompt)?

## Motivation

Reel `DfXFwwCDFMD` (alvim_ai, transcript
`.devin/scratch/reels-7/transcripts/DfXFwwCDFMD.txt`, survey row 9 of
`.devin/research/2026-11-10-reels-batch7-survey.md`) promotes a Claude Code
plugin ("LGPD Skills", e.g. `lgpd-compliance-falkzera`) that opens an audit
questionnaire against a project: app-store registration questions,
mandatory-permission justification, third-party SDK data sharing,
subject-request SLA (15 days), log masking, double-confirmation on paid
actions, and breach notification to the ANPD (3 days). Penalty cap cited:
R$50M per infraction (LGPD Art. 52).

## What exists in the bundle today

Verified by grep (`lgpd|dpia|privacy|pii` across `skills/`, `.devin/docs/`,
`extensions/`):

- `skills/security-audit/SKILL.md` - SAST, dependency scanning, secret
  leaks, OWASP-style checks. Attack-surface focus, no data-protection
  questionnaire.
- `skills/security-audit-cf/` - vendored Cloudflare audit workflow
  (six-phase vuln hunting, `report-schema.json`). No privacy/DPIA coverage.
- `skills/secure-defaults-check/` - pre-commit checklist for secure
  defaults (hidden credentials, confirmation on destructive actions).
  Adjacent in spirit (the reel's "double confirmation on pay" item maps
  here) but not a compliance artifact generator.
- `skills/security/` - general security router.

Gap: nothing produces a data-inventory / legal-basis / subject-rights
matrix. The `security-audit` flow has a findings report but no
DPIA/LGPD-style questionnaire - the "DPIA/LGPD matrix" presumed in the
issue does not exist; the closest anchors are the audit report-schema and
the secure-defaults checklist.

## Case for a reusable skill

- The questionnaire is repeatable: the same ~10 question groups apply to
  every app handling personal data of Brazilian users.
- Answers are repo-grounded: third-party deps, permission manifests,
  logging paths, and payment flows are all discoverable in source - a
  good fit for an agent-led checklist rather than a blank form.
- Output is a document (compliance matrix), matching the bundle's
  "findings + verification command" report convention.
- Jurisdiction scoping: LGPD structure maps closely to GDPR/CCPA, so one
  skill with a jurisdiction parameter avoids per-law forks.

## Proposed SKILL.md outline

- Frontmatter: `name: lgpd-questionnaire`, description triggering on
  LGPD/DPIA/compliance-review requests, `triggers: [user, model]`.
- `## When to use` - audit requests, pre-launch store review, new
  third-party SDK, data-subject complaint.
- `## Inputs` - jurisdiction (default LGPD), app surface (mobile, web,
  backend), optional manifest paths.
- `## Questionnaire groups` - (1) data inventory and legal basis,
  (2) permissions vs need-to-have, (3) third-party sharing register,
  (4) retention and minimization, (5) subject-rights handling (access,
  correction, deletion - 15-day SLA), (6) logging and masking,
  (7) consent and UX confirmations (incl. double-confirm on payment),
  (8) breach response (ANPD 3-day window, Art. 48).
- `## Evidence rules` - every answer cites file:line; unverifiable items
  marked `needs-owner`, never guessed.
- `## Output` - Markdown matrix (question, status, evidence, gap,
  remediation); severity ranked like security-audit findings.
- `## Boundaries` - produces a working draft for a DPO/lawyer review;
  not legal advice; does not modify code.

## Recommendation: in-bundle

1. Small - a questionnaire is one SKILL.md plus an optional report
   template; no runtime deps, no scripts. Fits the "smallest solution
   that works" rule.
2. Reusable across projects, which is what `skills/` is for; user-side
   copies would drift per project.
3. Composes with existing pieces: `security-audit` (overlap guard via
   "See also"), `secure-defaults-check` (UX confirmation items).
4. Jurisdiction parameter keeps it honest: default LGPD, same checklist
   serves GDPR-style reviews. Per-company details (DPO, ANPD contacts)
   stay in project context, not the skill.

Skeleton created at `skills/lgpd-questionnaire/SKILL.md` (sections and
prompts only; full question bank deferred to implementation).

## Sources

- `.devin/scratch/reels-7/transcripts/DfXFwwCDFMD.txt`
- `.devin/research/2026-11-10-reels-batch7-survey.md` rows 9 and R7-15
- `skills/security-audit/SKILL.md`, `skills/security-audit-cf/`,
  `skills/secure-defaults-check/`
