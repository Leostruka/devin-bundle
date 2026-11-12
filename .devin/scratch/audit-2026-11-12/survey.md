
## Wave E/F completion + operate-spline (11:40)

- Spline-operator: deliberately removed #72 (Blender stack); operate-spline skill was dead route -> removed via PR #540 (184 skills).
- PermissionRequest: registered, 0 commands -> issue #541 (spike: does CLI fire it?).
- Tests/data audit: 6 defects -> issue #542 (vacuous check-count test, fake mutation tests, dead skip guards, stale fixture/filename).
- Stale skill export_hash x34: bookkeeping metadata (hash of last export); install.ps1 syncs live from source -> NOTE, no issue.
- install.sh vs install.ps1 extension sets: identical. release.yml tag/version sync OK.
