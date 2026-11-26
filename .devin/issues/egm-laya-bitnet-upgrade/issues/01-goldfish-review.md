# Issue 01: Goldfish Review protocol + drift-audit

Status: resolved (protocol doc + profile updates landed 2026-10-31).

## Done

- `.devin/sdd/goldfish-review.md` canonical protocol + `drift-audit` design.
- `agents/reviewer.md` and `.devin/agents/repo-reviewer.md` carry the
  Goldfish section with mandatory `zoom-out` first check.
- Pre-review triage wiring documented: `extensions/laya-tools/review_gate.py`
  (7-question diff triage) and `extensions/laya-tools/doc_coverage.py`
  (explicit doc-to-test contract) are referenced by the protocol and
  reviewer profiles as advisory steps - they never auto-approve and never
  replace the zero-history dispatch.

## Open (future ticket)

- Use `skills/drift-report/SKILL.md` for `drift-audit`: an existing
  report-only workflow. A new reporter script is deferred unless a measured
  gap justifies it; no standalone command is installed.
