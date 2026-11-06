# de-slop: codebase-wide slop audit mode

status: resolved
priority: P3
source: reels batch-4 survey (.devin/research/2026-11-06-reels-batch4-survey.md)

## Evidence
voxaris_ai reel: 'Untangle Codebase' skill detects accumulated duplication, unnecessary wrappers, temp workarounds from long AI-coding sessions. de-slop today is diff-scoped (current changes only).

## Task
Add a 'codebase mode' section to de-slop: when asked to untangle/clean a whole codebase (not a diff), hunt accumulated duplication, needless wrappers, stale temp fixes; pair with big-file-refactor for >1k-line files.

## Answer

Added Codebase mode paragraph to skills/de-slop/SKILL.md Scope section.
