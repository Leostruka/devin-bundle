# Delegation contract

## Contract

- **Contract ID**: 08-implementer-rag-fix-s1
- **Objective**: Fix review findings S1 (Important) and S2 (Minor) from
  `.devin/research/rag-skill-review.md` in `skills/rag/`.
- **Profile**: implementer
- **Lane**: direct on main worktree
- **Inputs** (read first):
  - `D:\Programing\ai_workspace\devin-bundle\.devin\research\rag-skill-review.md`
    (the findings)
  - `D:\Programing\ai_workspace\devin-bundle\skills\rag\reference\eval-and-failures.md`
    line 11 - "30+ pairs minimum" violates the no-fixed-thresholds rule
  - `D:\Programing\ai_workspace\devin-bundle\.devin\research\rag-practices.md`
    self-quiz 2a (~line 407): numeric thresholds must be taught as
    "measure on your corpus", never fixed numbers
  - `D:\Programing\ai_workspace\devin-bundle\skills\rag\SKILL.md` line ~57 -
    (C36) citation for the FTS5 compiled-check is loose
- **Readable refs**: `.devin/adr/004-rag-skill-tier-model.md`
- **Frozen inputs** (re-hashed at verify; drift fails the contract):
  - `.devin/research/rag-practices.md` sha256:04960e75164406fc5b8aa0a3ac25989a332871c5e9bb443a6aa460ae1d60c09d
  - `.devin/research/rag-skill-review.md` sha256:1a9a066c347e695942fcf1f441891d28fc1516340c1880876320eee75db49efb
- **Output**: two surgical edits + handoff at
  `.devin/handoffs/08-implementer-rag-fix-s1-out.md`
- **Files you may modify (exclusive)**:
  - `skills/rag/reference/eval-and-failures.md` - S1: replace the fixed
    "30+ pairs minimum" floor with corpus-relative sizing guidance (pairs
    covering each distinct corpus intent + paraphrase/adversarial cases;
    sized by corpus coverage, not a universal number; grown over time is
    fine to keep). Keep the golden-set-first teaching intact.
  - `skills/rag/SKILL.md` - S2 (Minor): tighten the C36 citation so the
    platform-dependence of a compiled-in FTS5 is explicit in the practice
    (e.g., "verify the target Python ships FTS5" wording). One-line-class
    edit; do not restructure the file.
  - `manifest.json` - resync the `scripts` entry hash for
    `scripts/validate-tool-args.py` (contract 03 edited the script;
    audit.py reports "manifest script hash mismatch" warning). Compute the
    script's current hash the same way audit.py does and update only that
    field. Nothing else in the file.
- **Tools allowed**: profile default
- **Peer consults**: none
- **Boundaries (do NOT)**: touch audit.py, docs/, or any file beyond the
  three listed above; modify manifest.json fields other than the
  validate-tool-args.py script hash; restructure beyond the two findings;
  introduce fixed
  thresholds elsewhere; add vendor names or em-dashes (U+2014 - the repo
  stop-guard blocks them in prose position; use "- " or rewrite naturally)
- **Termination**: max 15 turns / 15 minutes; stop when VFs pass
- **Verification (VFs)**:
  - VF1: `grep -n "30+" skills/rag/reference/eval-and-failures.md` -> gone
    or clearly reframed as corpus-relative (your call; report which)
  - VF2: `python scripts/validate-skill-format.py skills/` -> rag PASS
  - VF3: no prose-position U+2014 in the edited files
    (`grep -P "\x{2014}" skills/rag/ -r` clean or structural-only)
  - VF4: `python audit.py` -> 0 errors AND the
    "manifest script hash mismatch: validate-tool-args.py" warning is gone

## Result (orchestrator fills after return)

- status:
- VFs re-run independently:
- ledger line appended:
