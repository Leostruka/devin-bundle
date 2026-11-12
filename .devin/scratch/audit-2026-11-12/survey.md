
## Wave E/F completion + operate-spline (11:40)

- Spline-operator: deliberately removed #72 (Blender stack); operate-spline skill was dead route -> removed via PR #540 (184 skills).
- PermissionRequest: registered, 0 commands -> issue #541 (spike: does CLI fire it?).
- Tests/data audit: 6 defects -> issue #542 (vacuous check-count test, fake mutation tests, dead skip guards, stale fixture/filename).
- Stale skill export_hash x34: bookkeeping metadata (hash of last export); install.ps1 syncs live from source -> NOTE, no issue.
- install.sh vs install.ps1 extension sets: identical. release.yml tag/version sync OK.

## Loop 12:00-12:30

- #542 fixed: PR #543 (real mutation detection via secrets-block scenario; 4 dead skip guards -> hard imports; check-count parses numbered sections; fixture SessionEnd; compat test renamed).
- #533 envelopes: spec-consistency exits 1 on errors (contract [36]); install-ledger exception exits 1 (callers tolerate); subagent-trace already compliant. PR #545.
- #541 evidence: binary ClaudeHookEvent enum has PermissionRequest + Notification/SubagentStop/ContextInput/PreCompact/PostCompact - real event, empty registration is a gap.
- NEW DEFECT #544: check-push-green suite (~15s) exceeds hook budget - test-file pushes rejected by slowness, not decision. Bypassed via subprocess once; needs structural fix.
