# evaluate a file-size guard hook (warn on >N-line files in diff)

status: open
priority: P3
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Same reels 05/13 pain: oversized files rot context. A hook can warn when a diff grows a file past a threshold, complementing R2-05's refactor skill.

## Recommendation
Eval issue: add a soft-warning check to `pre-exec-guard` or a pre-commit path that flags files crossing a line threshold (configurable, fail-soft WARN not block - large files exist legitimately). Decide threshold per language or flat ~800 lines. Implement only if eval shows it does not spam; report as issue answer either way.

## Verification
Hook change (or documented skip) + a test in tests/validation.
