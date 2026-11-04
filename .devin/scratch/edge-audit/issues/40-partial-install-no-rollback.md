# 40 -- Partial installs: warn-and-continue leaves degraded installs with no record or rollback

- **Status**: open
- **Category**: adaptability
- **Severity**: P2
- **File**: install.ps1:530-538, install.sh:379-386, 546-558

## Evidence

Installers degrade gracefully but leave no durable record: `python not found - config.json hooks not rendered` (install.ps1:538, install.sh:386), `python not found - skipping <ext> venv` (install.ps1:652, install.sh:553). Result: an install can "succeed" with hooks unrendered (guardrails silently absent while hooks.v1.json exists at project level only) and extension venvs missing. There is no manifest of completed steps, no `--verify` mode that re-checks a prior install, and no rollback if a later step throws mid-install (e.g. `throw "AGENTS.md not found"` at install.ps1:445 fires before writes, but a mid-run failure after file copies leaves a half-installed home dir).

## Recommendation

Write an install receipt (`%APPDATA%/devin/.install-receipt.json`): steps attempted, skipped (with reason), failed; add `install.ps1 -Verify`/`audit.py` check that replays expected vs recorded state and reports degraded installs prominently rather than as warnings scrolled past.

## Tradeoffs

- Merits of warn-and-continue: install never hard-fails on missing optional deps; works on machines without python for the docs/rules payload.
- Demerits: the degraded state is invisible after the scroll buffer; hooks-not-rendered means the guardrail layer (fail_closed PreToolUse) is absent while everything else looks installed; a receipt adds a write that must itself be failure-tolerant (same class of problem as the planned ledger).
- Better contorno: make the last install step unconditionally print a summary of skipped steps (no new state file) as the floor; receipt/ledger upgrades it to auditable.

## Verification

Simulate with `PATH` stripped of python in a redirected-APPDATA dry run; confirm exit code is still success and no record of the skips persists.
