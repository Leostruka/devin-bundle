# devin-bundle

[![CI](https://github.com/Leostruka/devin-bundle/actions/workflows/ci.yml/badge.svg)](https://github.com/Leostruka/devin-bundle/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Skills](https://img.shields.io/badge/skills-48-blue.svg)](SKILL-TIERS.md)
[![Rules](https://img.shields.io/badge/rules-20-green.svg)](AGENTS.md)
[![Version](https://img.shields.io/badge/version-2.5.0-orange.svg)](CHANGELOG.md)

Export + installer for [Devin CLI](https://devin.ai) to synchronize your **entire setup** across machines.
Bundles skills, consolidated rules, config, hooks, scripts, MCP, and credentials —
restores everything to the correct destination with a single command.

The source of truth is the code: `AGENTS.md` (rules), `manifest.json` (skill count),
`hooks.v1.json` + `scripts/` (hooks), `audit.py` (validation). This README is a thin
navigation layer; for detail, read the source.

---

## Quick start

```bash
git clone https://github.com/Leostruka/devin-bundle.git
cd devin-bundle
./install.sh --force          # Linux / macOS / WSL
.\install.ps1 -Force          # Windows (PowerShell)
```

## Prerequisites

| Requirement | Why | Check |
|---|---|---|
| [Devin CLI](https://devin.ai) | The agent this bundle configures | `devin --version` |
| Python 3.8+ | Hook scripts are Python | `python --version` |
| Git | Versioning and cloning | `git --version` |

## Install

```powershell
.\install.ps1                    # install all (skip existing, merge config)
.\install.ps1 -DryRun            # show what it would do
.\install.ps1 -Force             # overwrite differences
.\install.ps1 -Force -Backup     # overwrite, saving backup first
.\install.ps1 -RestoreSecrets    # also install credentials.toml (if unmasked)
```
Destination: `%APPDATA%\devin\`

```bash
chmod +x install.sh
./install.sh                     # install
./install.sh --dry-run           # show only
./install.sh --force             # overwrite
./install.sh --restore-secrets   # install credentials.toml
```
Destination: `${XDG_CONFIG_HOME:-~/.config}/devin/`

The installer is idempotent — re-running only updates what changed (with `-Force`).
For step-by-step behavior, read `install.ps1` / `install.sh`.

## Export (regenerate bundle from source machine)

```powershell
.\export.ps1                    # export with secrets MASKED
.\export.ps1 -DryRun            # show what it would do
.\export.ps1 -Commit -Push      # export + validate + commit + push
.\export.ps1 -NoMask -Commit    # real secrets + commit (DO NOT push to public repo)
```

```bash
chmod +x export.sh
./export.sh                     # export with secrets MASKED
./export.sh --dry-run           # show only
./export.sh --commit --push     # export + validate + commit + push
./export.sh --no-mask --commit  # real secrets + commit
```

**WARNING:** `-NoMask` exports real secrets. NEVER push to a public repo with `-NoMask`.
For masking rules per file, read `export.ps1` / `export.sh`.

## Sync machines

Normal Git repo:
```bash
git clone <your-repo> devin-bundle
cd devin-bundle
./install.sh --force          # or install.ps1 -Force on Windows
```
To restore `credentials.toml`: `.\export.ps1 -NoMask` on source (DO NOT push),
transfer manually, `.\install.ps1 -RestoreSecrets` on target.

## Documentation

| Document | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | The 18 rules (loaded by Devin CLI every session) |
| [SKILL-TIERS.md](SKILL-TIERS.md) | Skills by domain of use + token costs (fast discovery) |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [SECURITY.md](SECURITY.md) | Security policy |

For skill count, hook list, or rule details, read the source files — not this README.

## License

[MIT](LICENSE) — 2026 Leostruka
