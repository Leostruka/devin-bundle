# Install/export parity contract

`install.ps1`/`install.sh` and `export.ps1`/`export.sh` are two language
implementations of one behavior contract. This table is the contract:
any change to a row must land in both scripts in the same change.

Legend: ps1 = install.ps1/export.ps1 (Windows), sh = install.sh/export.sh
(POSIX: Linux, macOS, WSL).

## Install contract

| Feature | Contract | ps1 | sh |
|---|---|---|---|
| Target dir | `%APPDATA%\devin` / `~/.config/devin` (`DEVIN_HOME` override) | yes | yes |
| Dry run | `-DryRun` / `--dry-run`: report only, no writes | yes | yes |
| Default mode | merge + skip existing user config | yes | yes |
| Force | `-Force` / `--force`: overwrite existing | yes | yes |
| Backup | `-Backup` / `--backup`: copy targets aside before overwrite | yes | yes (dirs: see known gap) |
| Credentials | copied only behind explicit flag | yes | yes |
| Hooks render | `python scripts/render-user-hooks.py` writes `config.json.hooks` from `hooks.v1.json` | yes | yes |
| Python detect | `py` launcher fallback / `python3` then `python` | yes | yes |
| AGENTS.md case-dedup | remove `agents.md`/`Agents.md` duplicates next to `AGENTS.md` | yes | gap |
| Restore secrets | only with explicit restore flag; masked placeholders never written as real | yes | yes |
| Report | installed / overwritten / merged / skipped / backed-up counts | yes | yes |

## Export contract

| Feature | Contract | ps1 | sh |
|---|---|---|---|
| Masking default | secrets -> `MASKED` unless `-NoMask` / `--no-mask` | yes | yes |
| Masked keys | `credentials.toml` all values; `config.json` `org_id`; `mcp_config.json` token/secret/key/password/auth/bearer/credential/private/pat env values; `https://user:pass@` URLs | yes | yes (regex dialect differs) |
| Hooks | `config.json.hooks` stripped on export; `hooks.v1.json` is source | yes | yes |
| Skill discovery | live skills dir -> `manifest.json` entries with `export_hash` | yes | yes |
| Folder hash | deterministic over file names + contents | yes | filenames gap (see audit) |
| Commit/push | opt-in flags only; never push unmasked to a public remote | yes | yes |
| Byte hygiene | no `__pycache__`/`.pyc` written into the repo by export | yes | pycompile gap |

## Rules for contributors

1. A fix to any row above lands in both scripts or files a tracked issue
   explaining the platform split.
2. New flags get a paired spelling (`-Flag` / `--flag`) and identical
   defaults.
3. Regex changes on one side require re-checking the other dialect
   (PowerShell `-replace` vs POSIX `sed` semantics differ).
4. Known divergences are tracked as scratch issues
   (`.devin/scratch/edge-audit/issues/`): sh backup silent-noop for
   directories (05), ps1-vs-sh masking asymmetry (06), sh pycompile
   dirtying scripts (09), folder-hash filename gap (08), AGENTS.md
   case-dedup (35), force-drift on masked mcp entries (12).
5. Long-term direction (accepted target, not yet scheduled): thin native
   wrappers over a shared `scripts/install_core.py` / `export_core.py`,
   matching how hook rendering is already centralized in
   `render-user-hooks.py`.
