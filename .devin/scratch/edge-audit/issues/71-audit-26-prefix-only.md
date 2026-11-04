# 71 -- audit check 26 compares only the first 60 chars, and only for "Use when" skills

- **Status**: open
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
