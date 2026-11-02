# R8-03: install.ps1 lacks the empty-extension-dir guard

**Severity:** P3 (parity with R6 fix)
**File:** install.ps1:~624 extensions loop

**Defect:** install.sh (R6) skips extension dirs with no files and
reports "is empty". install.ps1 iterates every dir and reports
"installed" for empty ones (e.g. spline-operator).

**Fix:** skip dirs where `Get-ChildItem -Recurse -File` finds nothing;
report "is empty".
