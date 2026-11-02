# R10-01: no [Unreleased] section — 7 merged PRs undocumented

**Severity:** P3 (user-facing docs)
**File:** CHANGELOG.md

**Defect:** since the v3.17.0 tag (2026-10-30) seven PRs merged to main
(#265 notes/model-guide, #266 agentic-rag vectorless selector,
#267 brag portfolio template, #268 exporter secret-masking + cwd +
staging fixes, #269 Windows %APPDATA% install target, #270 issue
answers, #271 TSF notes, #272 placeholder/identity fixes) with zero
CHANGELOG entries. Keep a Changelog convention puts [Unreleased] on
top; release.yml only requires `## [VER]` at release, so nothing
enforces it.

**Fix:** add `## [Unreleased]` section summarizing the merges under
Added/Fixed/Changed.

## Answer

Added `## [Unreleased]` documenting all 21 post-v3.17.0 merges under
Fixed/Added/Changed/Documentation. release.yml extractor (`## [VER]`
to next `## [`) unaffected.
