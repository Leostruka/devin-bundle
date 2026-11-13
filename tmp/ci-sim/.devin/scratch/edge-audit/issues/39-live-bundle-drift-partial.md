# 39 -- Live-vs-bundle drift detection is hash-pair only, ledger planned but absent

- **Status**: resolved
- **Category**: adaptability
- **Severity**: P2
- **File**: audit.py:498-527

## Evidence

`audit.py` detects live-vs-bundle drift by hashing a fixed list of file pairs (518-527) and warning on mismatch. Gaps: (a) only listed pairs are compared, skills/agents installed into `%APPDATA%/devin` that were renamed or deleted bundle-side are invisible (no foreign-file detection); (b) no record of what was installed when, so a mismatch cannot be classified as user-edit vs stale-install vs partial-install; (c) `.devin/issues/MILESTONE_2_06_install_drift_ledger.md` specifies exactly this (installs.json + 5-state reconcile Current/Outdated/Modified/Removed/Foreign) but status is `planned`, not implemented; (d) shadow-dir handling (both `%APPDATA%/devin` and `~/.config/devin` existing) is warn-only (513-516).

## Recommendation

Implement MILESTONE_2_06 as scoped, or an interim cheap version: enumerate installed `skills/`, `agents/`, `scripts/` under the live dir and diff the file-name sets against the bundle manifest, reporting foreign/missing counts in `audit.py`.

## Tradeoffs

- Merits of current hash-pair check: zero state files, deterministic, catches the highest-value drift (config.json, AGENTS.md, hooks render).
- Demerits: silent on anything outside the pairs list; cannot distinguish "user customized" from "bundle updated"; no uninstall/prune safety (foreign files accumulate across versions); the ledger design adds a writes-on-install requirement that makes install non-idempotent if the ledger write fails.
- Better contorno: name-set diff gives 80% of reconcile value with no ledger writes; full 5-state reconcile can follow when backup semantics are designed.

## Verification

`grep -n 'pairs' audit.py` shows the fixed list; `grep -rn 'installs.json\|reconcile' scripts/` returns nothing implemented.

## Answer

Wrote `.devin/docs/DRIFT-LEDGER.md`: freezes the MILESTONE_2_06 design (installs.json schema, rendered_hash rules, backup_if_differs, 5-state reconcile Current/Outdated/Modified/Removed/Foreign) plus the interim name-set-diff reconcile; links the milestone file as the implementation spec.
