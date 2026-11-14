# 71 -- audit check 26 compares only the first 60 chars, and only for "Use when" skills

- **Status**: resolved
- **Category**: algorithm-translation
- **Severity**: P2
- **File**: audit.py:802-824

## Evidence

The manifest-purpose sync check requires both `purpose` and the SKILL.md
description to start with "Use when" (line 817) and then compares only
`[:60]` (line 818). Two drift classes pass silently:

- Skills whose manifest purpose does not start with "Use when" are skipped
  entirely, so purpose/description can diverge arbitrarily.
- Purposes that diverge after character 60 report a match; a truncated or
  rewritten tail is invisible.

The documented contract ("manifest purpose matches SKILL.md description") is
implemented as "60-char prefix equality on a subset of skills".

## Recommendation

Compare normalized full strings (collapse whitespace) for all skills, and
emit a warning (not error) when one side lacks the "Use when" prefix so the
skipped set is visible.

## Verification

Edit a manifest purpose's text after char 60, keep the prefix; `python
audit.py` check 26 stays OK.

## Answer
Check 26 now compares whitespace-normalized FULL strings (manifest purpose
vs SKILL.md description) instead of the 60-char prefix, and emits a warning
listing skills that lack the `Use when` prefix (6 currently: brag,
brag-slim, thermos, typescript-best-practices, unslop,
vercel-react-best-practices) so the skipped set is visible. The one real
drift found (agent-reach) was fixed by aligning the SKILL.md description
with the manifest purpose.
