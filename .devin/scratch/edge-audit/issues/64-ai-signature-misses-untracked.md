# 64 -- AI-signature Stop scan never sees untracked files

- **Status**: open
- **Category**: applied-rules
- **Severity**: P2
- **File**: scripts/check-ai-signature.py:140-143

## Evidence

`handle_stop` scans only `git diff --cached` and `git diff`. A brand-new file
that was never `git add`ed produces no diff output, so a signature string
written into a new deliverable escapes the Stop gate entirely. The PreToolUse
write/edit path catches signatures at write time, but content appended via
exec redirects (`cat > file`, heredoc) is invisible to that path and also
invisible to the Stop scan while the file remains untracked.

## Recommendation

Add `git ls-files --others --exclude-standard` to the Stop scan and check the
contents of new files (bounded size) against `PATTERN`.

## Verification

Write a new file containing a signature line via exec redirect, do not stage
it, then send a Stop payload; the hook exits 0 instead of blocking.
