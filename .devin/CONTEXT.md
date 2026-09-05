# Devin Bundle Context

## Purpose

`devin-bundle` versions and synchronizes a Devin CLI setup across machines. It distributes rules, skills, agent profiles, hooks, scripts, configuration templates, and metadata through cross-platform installers and exporters.

## Users

- Bundle maintainer: curates and exports the canonical setup.
- Bundle installer: restores the setup on Windows, Linux, macOS, or WSL.
- Devin CLI agent: consumes installed rules, skills, profiles, hooks, and configuration.

## Core concepts

| Term | Meaning |
|---|---|
| Bundle | The Git-tracked repository containing distributable Devin CLI resources. |
| Live configuration | The user-level Devin CLI configuration under `%APPDATA%/devin/` or `~/.config/devin/`. |
| Export | Synchronizing live configuration into this repository while masking secrets by default. |
| Install | Synchronizing repository resources into the live configuration. |
| Skill | An invocable workflow stored at `skills/<name>/SKILL.md`. |
| Agent profile | A reusable subagent definition stored under `agents/`. |
| Hook | A command attached to a Devin CLI lifecycle event. |
| Manifest | `manifest.json`, the metadata inventory for bundle skills and targets. |
| Masked value | A secret-bearing configuration value replaced before distribution. |
| Held-out test | A test outside the refinement-selected validation set, used to detect illusory gains. |

## Boundaries

The bundle owns:

- Cross-platform export and installation behavior.
- Distributable global rules, skills, agents, hook scripts, and templates.
- Validation of structural consistency and safety constraints.

The bundle does not own:

- Devin CLI runtime implementation.
- Real credentials or private configuration values.
- Application code for projects consuming the bundle.

## Main flows

### Export

1. Read the live Devin CLI configuration.
2. Discover skills from the live skills directory.
3. Mask configured secret-bearing values unless explicitly disabled.
4. Update repository artifacts.
5. Validate before optional commit or push.

### Install

1. Read repository artifacts.
2. Create the target Devin CLI configuration directory.
3. Copy, merge, skip, or overwrite resources according to flags.
4. Restore secrets only when explicitly requested.
5. Report installed, overwritten, merged, skipped, and backed-up resources.

### Validate

1. Run `python audit.py` for bundle consistency.
2. Run `python -m pytest` for validation and held-out behavior.
3. Run exporter dry-run checks when exportable resources change.

## Invariants

- Deliverables contain no AI signatures.
- Pushes require green local checks.
- Secret values remain masked in distributable artifacts.
- Skill directory names match skill frontmatter names.
- Manifest skill names and on-disk skill directories remain synchronized.
- Windows and Unix workflows remain supported.
- Refinement claims require reproducible evidence and held-out validation.

## Important files

| Path | Role |
|---|---|
| `AGENTS.md` | Canonical global behavior rules distributed by the bundle. |
| `manifest.json` | Bundle metadata and skill inventory. |
| `config.json` | Masked Devin CLI configuration template. |
| `hooks.v1.json` | Project-level lifecycle hook template. |
| `install.ps1`, `install.sh` | Cross-platform installers. |
| `export.ps1`, `export.sh` | Cross-platform exporters. |
| `audit.py` | Bundle consistency audit. |
| `.github/workflows/ci.yml` | CI validation source. |
| `docs/plans/` | Approved implementation roadmaps and sub-plans. |

## Branch policy

The repository uses two tracks: **direct** and **experimental**.

- **Direct track:** short-lived branches target `main`. Use this for verified maintenance fixes and approved production work. Open a PR to `main`; do not push or merge without explicit human authorization.
- **Experimental track:** short-lived branches target `experimental`. Use this for unvalidated agent-harness ideas, prototypes, and speculative improvements. `experimental` must always contain everything from `main`.
- **Synchronization:** before starting experimental work and after every relevant `main` update, synchronize `main` into `experimental` (`git merge-base --is-ancestor main experimental` must exit 0).
- **Promotion:** experimental behavior reaches `main` only through a separate promotion issue backed by reproducible evidence, held-out tests, no regression, and acceptable context cost. Promotions create their own short-lived branches from current `main`.
- **No direct commits or pushes to `main` or `master`:** all changes land through PRs with explicit authorization.
