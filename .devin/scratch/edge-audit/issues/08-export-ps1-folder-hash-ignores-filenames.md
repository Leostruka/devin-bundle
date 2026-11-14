# 08 -- export.ps1 Get-FolderHash hashes contents only; renames go undetected
- **Status**: resolved
- **Category**: code-optimization
- **Severity**: P2
- **File**: export.ps1:91-97

## Evidence
`Get-FolderHash` joins `(Get-FileHash $_.FullName).Hash` for sorted files;
the relative path is not part of the hashed material. install.ps1's copy of
this function (install.ps1:103-116) explicitly includes
`hash + "  ./" + relpath` with the comment "a pure rename must change the
folder hash" -- that fix was applied to the installer but not the exporter.

Consequence: rename a file inside a live skill (e.g. SKILL helper renamed,
same content). src hash == dst hash, export reports "unchanged", and the
bundle keeps the old filename forever while the new file is never exported
(report_stale only warns about bundle-only TOP-level entries, not files
inside skill dirs).

## Recommendation
Copy the install.ps1 implementation: hash each file's content plus its
relative path before joining. One shared function definition (or keep both
files byte-identical for this helper).

## Tradeoffs
None; strictly more accurate change detection.

## Verification
Create skill dir with a.md; export; rename a.md -> b.md in $devinHome skills;
re-run export.ps1; assert the skill is re-exported (b.md present, a.md gone).

## Answer
export.ps1 Get-FolderHash now mirrors install.ps1: accepts $exclude, resolves a $base path, and hashes `content-hash + "  ./" + relpath` per file so pure renames change the folder hash. Skills export passes $skillExclude ('\__pycache__\|\.pyc$') to both hash calls. Covered by tests/test_export_ps1_edge_audit.py.
