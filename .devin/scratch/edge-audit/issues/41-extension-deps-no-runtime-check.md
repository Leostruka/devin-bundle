# 41 -- Missing extension deps: venvs built at install, never re-validated at use time

- **Status**: resolved
- **Category**: adaptability
- **Severity**: P2
- **File**: install.ps1:644-660, extensions/*/requirements.txt

## Evidence

Extensions with pip deps (`computer-use`, `media-tools`, `ai-tools`, `laya-tools`, ...) get a per-extension `.venv` created at install only when python is found (install.ps1:644-660); venvs are gitignored (`extensions/*/.venv/`). Nothing re-validates: a venv deleted, created with a different python minor, or half-created (pip failure mid-install) leaves the extension broken until its first call, and the failure surfaces inside the extension, not at a known checkpoint. `audit.py` has no extension-health section. Rust-core (ADR 003) builds at install time similarly with no post-build verification recorded.

## Recommendation

Add an `audit.py` section `Extensions:` iterating extensions with `requirements.txt`, checking `.venv` existence plus `pip check` (or a marker file of installed reqs hash) and reporting ready/degraded per extension. Optionally a shared `scripts/ext-venv-check.py` extensions call before work.

## Tradeoffs

- Merits of current approach: venv-per-extension isolates dep conflicts; gitignoring venvs keeps the repo clean; install-time build matches "artifacts build at install, never shipped" (ADR 003).
- Demerits: N venvs duplicate interpreter/site-packages disk cost; install-time-only validation means drift (deleted venv, python upgrade breaking shim) is invisible; `pip check` per extension is slow if run every audit (cache by requirements hash).
- Better contorno: a single shared venv with per-extension extras is possible but loses isolation; the marker-file approach (hash of requirements.txt stored post-install) is the cheap middle ground.

## Verification

`find extensions -name requirements.txt` lists dep-bearing extensions; `grep -n 'venv' audit.py` shows no check; delete one `.venv` and confirm audit stays green today.

## Answer
install.ps1: after a successful pip install, the requirements.txt SHA256 is written to .venv/.deps.sha256. New section 8a2 re-validates every dep-bearing extension under the target each install: missing venv, missing marker, or marker/requirements hash drift each produce a targeted warn ('re-run install to repair'); verified venvs report skip. Fail-soft, cheap (file hash only, no pip check). Covered by tests/test_install_ps1_edge_audit.py.
