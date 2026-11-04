# 38 -- CLI version drift: adequacao plans are manual, no runtime version check

- **Status**: open
- **Category**: adaptability
- **Severity**: P2
- **File**: data/bundle-identity.json, .devin/plans/2026-*.md

## Evidence

Version drift is handled by a manual adequacao workflow: `.devin/plans/2026-08-29-adequacao-devin-cli-3000.6.7.md` through `2026-10-30-adequacao-devin-cli-3000.11.234.md` (5 plans, each hand-verified with `devin --version`, `devin doctor`, changelog reading). `data/bundle-identity.json` pins `validated_cli_version: 3000.11.234`, but nothing at runtime compares the installed CLI against it: `session-start.py` and other hooks do not run `devin --version`, `config.json` has `auto_update: true` so the CLI can advance past the validated version silently, and DEVIN-CLI-COMPATIBILITY.md documents capabilities per version only as a changelog table.

## Recommendation

Add a lightweight check in `session-start.py` (or `audit.py`): compare `devin --version` output to `validated_cli_version`; on mismatch, print a one-line notice pointing at the adequacao plan pattern. Cheap, no blocking.

## Tradeoffs

- Merits of current approach: adequacao plans produce high-quality verified capability tables; auto_update keeps users on security fixes; no runtime coupling means hooks never break on a new CLI.
- Demerits: silent drift window between CLI upgrade and next adequacao run; hook/permissions contract changes (e.g. the fail_closed field, keymap validation) are discovered retroactively; a subprocess spawn in session-start adds latency and a failure path when devin is not on PATH inside the hook shell.
- Better contorno: gate only on `major.minor` mismatch, cache the result per session_id, fail open; keeps the manual deep-review while closing the awareness gap.

## Verification

`grep -rn 'devin --version\|validated_cli_version' scripts/` returns no runtime check; `grep -n 'auto_update' config.json`.
