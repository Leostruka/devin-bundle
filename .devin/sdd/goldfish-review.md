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

## `drift-audit` workflow (design)

Compare docs/ADRs against the real state on disk. Detection only; fixes land
in a follow-up ticket after user approval.

1. **Collect claims**: grep docs (`.devin/adr/*.md`, `.devin/CONTEXT.md`,
   `ARCHITECTURE_MANIFEST.md`, `.devin/docs/*.md`) for path references,
   model names, counts ("N scripts", "M tools"), and status markers.
2. **Resolve on disk**: each referenced path/name must exist; each count
   must match (`ls`, `grep`, `manifest.json`).
3. **Report**: `.devin/notes/drift-report-<date>.md` with a table
   `doc:line | claim | observed | proposed fix`. Never auto-edits.

Exit verdicts: `CLEAN` (no divergences), `DRIFT(n)` (n findings with
proposed diffs). Compose with the `drift-report` skill for ad-hoc runs.
