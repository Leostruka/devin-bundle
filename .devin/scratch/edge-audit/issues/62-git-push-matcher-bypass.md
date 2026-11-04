# 62 -- git push detection is a brittle substring match

- **Status**: open
- **Category**: applied-rules
- **Severity**: P2
- **File**: scripts/check-push-green.py:164

## Evidence

The gate triggers only when `"git push" in command.lower()`. These all bypass
it while still pushing:

- `git  push` / `git\tpush` (whitespace variants)
- `git -C repo push` or `git -c x=y push` (flag between verb)
- `alias gp="git push"`; `VAR="push"; git $VAR`
- `git push` inside a quoted string is caught, but `git remote update` and
  `git publish`-style custom verbs are not.

The matcher also only inspects `tool_name == "exec"` (line 159), so pushes
issued through any other tool surface (MCP git tools, write of a pre-push
script) are uncovered.

## Recommendation

Tokenize the command and match the git verb positionally (`git` followed by
optional global flags then `push`), or run the check on a server-side pre-push
hook instead of string-matching agent commands.

## Verification

`python scripts/check-push-green.py` with stdin
`{"hook_event_name":"PreToolUse","tool_name":"exec","tool_input":{"command":"git -C . push"}}`
exits 0 without running any tests.
