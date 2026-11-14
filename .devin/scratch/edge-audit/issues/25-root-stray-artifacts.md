# 25 -- Root directory mixes distribution artifacts with personal launchers and debris
- **Status**: resolved
- **Category**: organization
- **Severity**: P3
- **File**: devin-N.cmd, devin-N.ps1, devin-session-launcher.ps1, pytest_full.log, __pycache__/, .worktrees/ (all at repo root)

## Evidence
`global_rules.md` states "Treat root files as distribution artifacts." The root currently contains:

- `devin-N.cmd` / `devin-N.ps1` / `devin-session-launcher.ps1`: a pt-BR personal session launcher ("Iniciando o devin...", "Mensagens centralizadas do launcher (pt-BR)") that requires PowerShell 7. These are user-machine utilities, not bundle resources; nothing in install.ps1/install.sh/manifest.json references them.
- `pytest_full.log` (16K), `__pycache__/`, `.worktrees/` (empty dir): ignored by `.gitignore` but present in the working tree; they also mean a zipped/exported copy of the repo carries debris.
- `mcp_config.json` and `mcp_config.json.example` coexist at root; `hooks.v1.json` is project-level but sits at root with no indication it must be copied into `.devin/` (install.sh:392 only prints a skip hint).

A new user cannot tell which root files are inputs to the installer versus the maintainer's local conveniences.

## Recommendation
Relocate the launcher trio under `.devin/` (e.g. `.devin/tools/` or `.devin/scratch/launcher/`) or document them in README as optional maintainer utilities. Delete `pytest_full.log` and `__pycache__/` from the working tree and add `git clean -fdX` to a maintenance note. Clarify `hooks.v1.json` placement in README or move it under `.devin/`.

## Tradeoffs
Merits: root becomes a clean manifest of installable resources. Demerits: any personal workflow calling `devin-N.cmd` from the repo root must adjust the path.

## Verification
`ls` repo root; `grep -rn "devin-N\|session-launcher" install.ps1 install.sh manifest.json export.ps1` returns no references.

## Answer
Partially applied; remainder documented as intentional:

- `devin-N.cmd` / `devin-N.ps1` / `devin-session-launcher.ps1`: kept at root. They are a documented, tested feature, not personal debris: README section "Launcher multi-instancia (devin-N)" documents them, and `tests/pester/Devin-N.Tests.ps1` loads `devin-N.ps1`/`devin-session-launcher.ps1` from `$repoRoot`. Relocating would break Pester tests and README instructions. Initial move to `.devin/tools/launcher/` was reverted.
- `pytest_full.log`, `__pycache__/`: already absent from the working tree (gitignored via `*.log`, `__pycache__/`); nothing to delete.
- `hooks.v1.json`: kept at root. `install.sh` renders hooks from `$BUNDLE_DIR/hooks.v1.json` and CONTRIBUTING hook standards reference it there; it is a distribution artifact.
- `mcp_config.json` + `.example`: ownership now documented in `CONTRIBUTING.md` (issue 17).

Decision: root now contains only distribution artifacts and repo-standard files (AGENTS/README/manifest/audit/tests dirs).
