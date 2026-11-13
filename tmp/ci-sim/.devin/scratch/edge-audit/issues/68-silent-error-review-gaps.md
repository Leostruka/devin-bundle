# 68 -- silent-error-review can drop a real failure line and never closes the loop

- **Status**: resolved
- **Category**: investigative-cycles
- **Severity**: P2
- **File**: scripts/silent-error-review.py:95-116, 134-141

## Evidence

Two gaps:

1. False negative: `signal_lines` strips a line when it matches a noise
   pattern AND an error pattern but not `strong_errors` (lines 108-113). The
   `N failed` pattern (line 50) is absent from `strong_errors`, so a pytest
   summary like `1 failed, 1 warning` is classified as noise and removed; if
   it was the only signal, the tool result passes unflagged.
2. Advisory only: `emit` writes `additionalContext` and always exits 0
   (lines 134-141). Nothing requires the agent to acknowledge or act on the
   finding; the review cycle terminates with evidence the agent may ignore,
   and there is no metric recording how often findings fire vs get fixed.

## Recommendation

Add the failure-count and exit-code patterns to `strong_errors`, and have the
hook append findings to the metrics sink (issue 67) so repeat-ignored
warnings are detectable.

## Verification

Feed a PostToolUse payload with `success:true` and output
`==== 1 failed, 1 warning in 2.0s ====`; the hook prints nothing.

## Answer
Both gaps closed: the non-zero failure-count and exit-code patterns
(`N failed`, `exit code N`, `exited with N`) were added to `strong_errors`,
so a line like `1 failed, 1 warning` survives noise stripping and is
flagged. Findings are also appended to the metrics sink (issue 67) as
`silent-error-review` events, making repeat-ignored warnings detectable.
