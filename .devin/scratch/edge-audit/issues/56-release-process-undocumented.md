# 56 -- Release/tag procedure exists only in release.yml, not documented

- **Status**: open
- **Category**: versioning
- **Severity**: P2
- **File**: .github/workflows/release.yml

## Evidence
release.yml enforces tag ancestry on main, manifest.json version == tag,
and a CHANGELOG `## [VER]` section; audit check 32 enforces [Unreleased]
PR coverage; tags v3.2.0..v3.18.0 exist. But CONTRIBUTING.md contains no
mention of release, tag, version, or [Unreleased] mechanics (grep for
`release|tag|version|Unreleased` returns nothing). The human-side
procedure is tribal: when to bump manifest version relative to merges,
whether [Unreleased] is renamed to [VER] in the release commit, who may
push the tag, and the required order (changelog section first, tag
second, or the workflow fails). Current history shows the convention
works, but a new maintainer has no written runbook.

## Recommendation
Add a `## Releasing` section to CONTRIBUTING.md: merge PRs under
[Unreleased] -> single release PR renaming the section to [VER] +
bumping manifest.json -> tag `vX.Y.Z` on main -> release.yml verifies
and creates the GitHub release.

## Verification
Follow the doc on a dry-run basis: each step maps to an existing
enforcement (audit 32, release.yml checks) with no gaps.
