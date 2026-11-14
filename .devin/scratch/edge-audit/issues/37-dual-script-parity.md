# 37 -- Windows/POSIX dual-script parity burden across install and export

- **Status**: resolved
- **Category**: adaptability
- **Severity**: P2
- **File**: install.ps1, install.sh, export.ps1, export.sh

## Evidence

Four entry points must stay behavior-identical in two languages: `install.ps1` (650+ lines) vs `install.sh`, `export.ps1` vs `export.sh`. Observed divergence surface: install.ps1 carries the AGENTS.md case-dedup logic (369-405) and `py` launcher fallback (644); install.sh detects python3/python differently (94-99, 546-553); masking regexes must be reimplemented per shell (export.ps1:159-165 vs export.sh equivalents). `audit.py` has parity-oriented checks (hook command normalization at 541-547) but no systematic diff of install/export behavior between the two scripts; parity drifts are found by manual review or adequacao plans.

## Recommendation

Move shared logic into the existing Python layer: a single `scripts/install_core.py`/`export_core.py` invoked by thin ps1/sh wrappers, matching how hook rendering is already centralized in `render-user-hooks.py`. Failing that, add a parity checklist test (feature table: dedup, hooks render, venv creation, masking rules) asserted for both scripts.

## Tradeoffs

- Merits of dual scripts: native UX per platform (powershell signing policy, bash on minimal POSIX), no Python dependency for the install bootstrap itself.
- Demerits: every fix lands twice or drifts; PowerShell/bash regex semantics differ (masking bugs); testing requires both platforms (Pester exists under tests/pester but coverage of sh is thinner); reviewers must read two dialects.
- Better contorno: the thin-wrapper approach keeps bootstrap native while making the risky logic single-sourced; python is already a hard dependency of the installed bundle (hooks call `python scripts/...`), so requiring it at install is consistent. Remaining burden: python may be absent pre-install, so wrappers must keep a degrade path.

## Verification

`wc -l install.ps1 install.sh export.ps1 export.sh`; `grep -c 'mask\|MASKED' export.sh` vs export.ps1; `ls tests/pester` vs sh test coverage.

## Answer

(sh parity part) Added tests/test_install_sh_parity.py: a static parity checklist asserting flag surfaces, credentials opt-in, masked-mcp --force, deep-merge semantics, hook rendering, masking vocabulary, push+no-mask gate, hooks-stripping, and pre-push validation all match the ps1 contract.

(doc part) Wrote `.devin/docs/INSTALL-PARITY.md`: full ps1-vs-sh contract table for install and export (dry-run, merge/skip, force, backup, credentials, hooks render, python detect, masking set, commit/push), the 5 parity rules for contributors, and the known-divergence list pointing at scratch issues 05/06/08/09/12/35.
