# Edge-audit execution plan

Resolve all 68 issues under `.devin/scratch/edge-audit/issues/` via parallel
implementer lanes on isolated worktrees, then integrate, version, install,
and ship to remote.

## Lane map (file-surface ownership, no cross-lane writes)

| Lane | Issues | Owns |
|------|--------|------|
| W | 01,02,03,04,05,06,07,09,11,12,16,18,19,20(sh part),36,37,38,40 | install.sh, export.sh, new tests test_install_sh_* / test_export_sh_* |
| X | 08,20(ps1 part),27,35,41 | install.ps1, export.ps1, new tests test_install_ps1_* |
| Y | 10,26,34,42,61,62,63,64,65,66,67,68,69,70,71 | scripts/*.py (gates/hooks), audit.py, render-user-hooks.py, existing gate tests |
| S | 76,77,78,79,80(see note),81,82,83 | extensions/, tests/infra (conftest, pytest.ini), new test files |
| Z | 21,22,31,32,33,37(doc),39,46-57,72 | .devin/docs/, .devin/adr/, README.md, TOOLS-MAP, mermaid diagrams |
| O | 17,23,24,25 | root files (mcp_config, debris), .gitignore, .devin/scratch hygiene, skill overlap doc |

Issue 80 (chmod 600 on credentials/mcp in install.sh) assigned to W; S skips it.
Issue 20 split: W fixes POSIX scripts, X fixes PS1.
Issue 37: W codifies parity checks in tests; Z writes the parity contract doc.
Issue 39 (drift ledger): Z documents + stub; runtime check part goes to W if simple.

## Shared files (integration-only, lanes must NOT touch)

manifest.json, CHANGELOG.md, .devin/docs/TOOLS-MAP.md (except Z), pytest.ini
(except S), hooks.v1.json (Y owns).

## Per-issue protocol (afk-loop)

claim -> implement TDD -> resolve with ## Answer -> Status: resolved.
Lanes update ONLY their own issue files.

## Integration

Merge lanes in order Z, O, X, S, Y, W (docs first, scripts last).
Then: manifest bump 3.19.0, CHANGELOG [Unreleased] -> release notes,
audit + full pytest green, tag per release.yml convention, PR, merge,
install -Force, doctor, final alignment.
