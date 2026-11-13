# 22 -- README is Portuguese-only and quick-start defaults to -Force
- **Status**: resolved
- **Category**: user-experience
- **Severity**: P3
- **File**: README.md:9-27

## Evidence
The entire README (intro, quick start, prerequisites, architecture explanation) is written in Portuguese ("Ecossistema versionado", "Inicio rapido", "Posuta padrao"), while all operational artifacts it documents (AGENTS.md rules, skill descriptions, installer messages, SKILL-TIERS.md) are English. A new user who does not read Portuguese cannot evaluate prerequisites or the merge/force semantics from the README.

The quick start also instructs `.\install.ps1 -Force` and `./install.sh --force` as the default invocation. `-Force`/`--force` bypasses the merge-and-skip safety behavior both installers build around existing user config (install.ps1:158-162, install.sh:218-224), and `--force` in install.sh combined with `--backup` silently skips backups for directories (see issue 05). Neither the README nor the quick start mentions `--dry-run` as the recommended first step, even though both scripts implement it.

## Recommendation
Add an English quick-start section (or a short bilingual header) covering: dry-run first, plain install for fresh machines, `--force --backup` only when overwriting an existing setup. Keep the Portuguese body if desired but the onboarding-critical 20 lines should be readable by the bundle's documented audience.

## Tradeoffs
Merits: lower onboarding friction, fewer accidental overwrites. Demerits: duplicated prose to maintain if both languages are kept.

## Verification
`head -30 README.md`; compare with `usage()` output of install.sh and the parameter block of install.ps1.

## Answer

Added an English `## Quick start` section before the Portuguese one: dry-run first, plain install for fresh machines, `-Force`/`--force` + `--backup` only for overwrites, with the same warnings mirrored in the Portuguese block.
