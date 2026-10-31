# Goldfish Review + drift-audit (EGM adapted)

Source pattern: Google EGM "Goldfish Review" (zero-chat-history review
subagent). Adapted to this bundle's SDD flow. The external EGM repo is NOT
installed; this file is the canonical protocol.

## Goldfish Review protocol

Dispatch a review subagent (profile `reviewer` or `repo-reviewer`) with a
context window containing ONLY:

1. The spec under review: `<spec-dir>/spec.md` (verbatim file, not a summary).
2. Pointers to the code/diff on disk (paths and commands like `git diff`).

Never include:

- The originating chat history or transcript.
- The implementer's own report or reasoning, including any appendix.
- Prior review rounds (each review is a fresh fish).

### Mandatory check order

1. **zoom-out**: does the repo/bundle already solve this problem with less
   code? If yes, that verdict dominates all other findings.
2. Spec compliance: does the diff do exactly what spec.md asks, no more?
3. Standards: project invariants (stdlib-only `scripts/`, fail_closed hooks,
   no secrets, ADR conventions, Rule 15 evidence).
4. Line-level findings, severity-calibrated.

### Output contract

```
ZOOM-OUT: <already-solved | gap-real>
SPEC: <met | partial | divergent> (cite spec.md lines)
STANDARDS: <violations, file:line>
FINDINGS: [severity] file:line - issue
VERDICT: approve | rework | reject
```

## Pre-review triage (advisory, implemented)

Before dispatching the review subagent, the orchestrator MAY run two
stdlib-only checks to enrich the brief. Their output is triage metadata
attached to the dispatch - never an approval, never a skip decision on its
own, and the dispatched reviewer still runs the full Goldfish check order.

1. Diff triage - `extensions/laya-tools/review_gate.py` (JEV-4):

   ```
   git diff > change.diff
   python extensions/laya-tools/review_gate.py --diff change.diff \
       --commit-msg-file msg.txt [--config .devin/laya/profile.json]
   ```

   Emits `{"risk": low|medium|high, "requires_deep_review": bool, ...}`.
   `risk=high` (secrets, protected paths, dependency changes) means the
   review dispatch is mandatory; `low` means the deterministic gate found
   nothing to escalate - it still does not authorize merge. The optional
   `review-risk-v1` shadow currently abstains `feature_off` because the
   profile is not enabled in `.devin/laya/profile.json`.

2. Doc coverage - `extensions/laya-tools/doc_coverage.py` (JEV-5): when the
   diff touches rules/docs/ADRs, check each changed doc against the
   shipped declared map `.devin/validation-contracts.json` (doc path ->
   executable test targets; covered by `test_jev_runtime_contracts.py`):

   ```
   python extensions/laya-tools/doc_coverage.py \
       --changed AGENTS.md .devin/rules/x.md \
       --map .devin/validation-contracts.json --tests-root .
   ```

   A changed doc without a valid contract is an `Important` finding to
   include in the review brief, never `Minor`.

These checks are deterministic and offline; they add no new automatic
execution or approval semantics to the protocol.

## `drift-audit` workflow (design)

No standalone command is installed. `drift-audit` names an invocation of
`skills/drift-report/SKILL.md`, the existing EGM-derived detection workflow.
Use that skill's report format; do not build a duplicate scanner. Target
`.devin/docs/`, `.devin/adr/` and `.devin/plans/` explicitly in this bundle.
Compare docs/ADRs against disk; detection only. Corrections belong to a
separate, authorized self-improvement step.

1. **Collect claims**: grep docs (`.devin/adr/*.md`, `.devin/CONTEXT.md`,
   `ARCHITECTURE_MANIFEST.md`, `.devin/docs/*.md`) for path references,
   model names, counts ("N scripts", "M tools"), and status markers.
2. **Resolve on disk**: each referenced path/name must exist; each count
   must match (`ls`, `grep`, `manifest.json`).
3. **Report**: `.devin/<YYYY-MM-DD>_DRIFT_REPORT.md`, following the
   existing skill's per-document format. Include doc:line, claim, observed
   state and proposed correction as evidence. Never auto-edit targets.

Exit verdicts: `CLEAN` (no divergences), `DRIFT(n)` (n findings with
proposed diffs). Compose with the `drift-report` skill for ad-hoc runs.
