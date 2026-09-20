# Task 12 report — integration, skill, docs

## Scope

`skills/system-control/SKILL.md` (49-line router),
`extensions/system-control/USAGE.md` (~160), validation test,
metadata sync (manifest 51→52, SKILL-TIERS, TOOLS-MAP, README).

## Delivered

- SKILL.md: `triggers: [user, model]`; routes to USAGE.md; states
  when system APIs beat GUI; preserves one-shot confirmation,
  deny-wins, untrusted-output, broker-unprovisioned rules.
- USAGE.md: interpreter, exit codes, JSON status semantics, policy
  classification, command×confirm matrix, platform matrix, sessions,
  files, telemetry, broker opt-in, failure modes, install, safe
  read-only examples. Required phrases present.
- `tests/validation/test_system_control_workflow.py`: 5 tests —
  router lines/ref/frontmatter, safe-default phrases, manifest
  entry, `extensions/*` enumeration in both installers.
- Installers unchanged: `extensions/*` glob already enumerates
  system-control (verified via dry-run).

## Review

Independent review: Security PASS, Standards PASS, Spec FAIL →
fixed:

1. Platform matrix dishonest — Windows `service.restart` is SCM
   direct under caller rights (confirm + `--allowed`), broker
   optional; Linux/macOS broker only. Corrected.
2. Export gap — `export.*` handle skills/config only, not
   local-tool extensions; rationale documented in USAGE.md
   ("sync via git, not export") per plan step 6.
3. README tree 51→52; unused pytest import removed.

## Verification

- Validation test: RED → GREEN, 5/5.
- Full suite: **949 passed, 3 skipped**.
- `python audit.py`: **0 errors** (manifest/badge/TOOLS-MAP/
  SKILL-TIERS/README all synced at 52).
- `bash -n install.sh`; `install.sh`/`export.sh` dry-runs exit 0,
  `would install extensions/system-control` + `skills/system-control`.
- install.ps1 ParseFile: 0 errors; `install.ps1 -DryRun`,
  `export.ps1 -DryRun` (pwsh 7) exit 0.

## Residuals

- `export.ps1 -DryRun` fails on legacy Windows PowerShell 5.1 on
  this host (stripped `Get-FileHash`) — pre-existing environment
  limitation, passes under pwsh 7.
- Temp-dir naming DoS note from security review (fail-closed only);
  optional per-UID hardening deferred.
