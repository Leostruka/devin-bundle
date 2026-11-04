# 66 -- Rules 25, 27, and the Rule 15 log have no enforcement mechanism

- **Status**: resolved
- **Category**: applied-rules
- **Severity**: P2
- **File**: n/a (AGENTS.md rules 25, 27, 15; no matching script)

## Evidence

- Rule 25 (no test deletion without approval): no hook inspects diffs for
  deleted test files or removed test functions. `grep` for "test deletion" /
  "Rule 25" across scripts/ and audit.py finds nothing.
- Rule 27 (declare intent before coding): no hook or audit check verifies an
  intent declaration precedes writes; it is purely behavioral.
- Rule 15 requires each refinement be logged to `.devin/refinements.log.jsonl`,
  but the only reference to that file in scripts/ is prompt text inside
  refine-review-prompt.py:58. No code writes the log; validate-refinement-
  evidence.py:199 exits cleanly with "No refinements.log.jsonl found", so the
  evidence standard validates nothing until the agent voluntarily creates the
  file.

## Recommendation

For Rule 25, add a Stop/pre-push check that flags `git diff` hunks deleting
lines from `tests/**` without an approval marker. For the refinements log,
have refine-review-prompt create/append the record itself when it fires.

## Tradeoffs

Rule 27 is inherently behavioral; enforcement would be a prompt-time nudge at
best. Cheap option: pre-write-guard emits additionalContext reminding the
agent to state intent when the session has none recorded.

## Verification

`grep -rn "tests/" scripts/check-push-green.py` shows no deletion check;
`ls .devin/refinements.log.jsonl` confirms absence while refine prompts have
already fired.

## Answer
Enforcement added on two fronts:
- Rule 25: check-push-green.py now blocks a push when `git status` shows
  deleted files under tests/ or the HEAD diff removes `def test_`/`class
  Test` lines, unless `.devin/test-deletion-approved` (or
  .devin/approvals/test-deletion.txt, or TEST_DELETION_APPROVED=1) exists.
- Rule 15 log: refine-review-prompt.py appends a `refine-reminder-*` record
  (with all required evidence keys) to .devin/refinements.log.jsonl when it
  fires, so the file exists and the firing is auditable.
Rule 27 (declare intent) remains behavioral by design - the issue itself
classifies it as prompt-level at best.
