# r14-changelog-01: [Unreleased] gap recreated by post-R10 merges

## Problem

R10 added `## [Unreleased]` covering 21 PRs through #273, but five merges since then are undocumented again — the same defect class recurring because changelog updates are manual and unchecked:

| Merge | PR | Missing entry |
|---|---|---|
| a7b5e70 | #274 | subprocess bounds in probe_spawnpty + media-tools tests |
| ab36da5 | #275 | recipes.json phantom `glob` tool removed |
| 3b0dccb | #276 | GG Coder video analysis notes |
| b3f502d | #277 | dispatching DeepSeek super-agent evidence |
| f253946 | #278 | manifest forbidden-crossing fix + import boundary test |

## Impact

CHANGELOG (user-facing release notes source for `release.yml` extraction) silently drifts from git reality; next release would ship notes missing five changes.

## Fix

Update `[Unreleased]` Fixed/Changed/Documentation sections with the five entries.
