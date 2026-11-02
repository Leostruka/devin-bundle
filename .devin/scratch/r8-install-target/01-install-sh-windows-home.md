# R8-01: install.sh has no Windows branch -- installs to a shadow dir

**Severity:** P1 (installs silently ineffective)
**File:** install.sh:166-168

**Defect:** `DEVIN_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/devin"` has no
Windows case. Under Git Bash/MSYS/Cygwin the Devin CLI reads
`%APPDATA%\devin`, but install.sh writes `~/.config/devin` -- a shadow
copy the CLI never loads. install.ps1 then deletes `~/.config/devin`
as "legacy".

**Evidence (this machine):** `%APPDATA%\devin` holds stale
`skills/brag/references/step-2-plan.md` and `skills/agentic-rag/SKILL.md`
(installed via install.sh after PRs #266/#267 never reached the real
config); `~/.config/devin` matches bundle.

**Fix:** detect MINGW*/MSYS*/CYGWIN* in `uname`; resolve
`DEVIN_HOME` to `%APPDATA%/devin` (cygpath when available, sed
backslash/drive-letter fallback otherwise).

## Answer

Fixed in PR #269; live `%APPDATA%\devin` synced by first corrected
install; regression asserts in `tests/validation/test_install_export_scripts.py`.
