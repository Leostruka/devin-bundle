# 01 -- memory-post-exec: unreadable note kills hook

- **Status**: resolved
- **Severity**: P2
- **File**: `scripts/memory-post-exec.py:102`

## Evidence

`notes.append(load_note(p))` runs unguarded inside the glob loop. One
non-UTF8 or unreadable `.md` in the memory dir raises
`UnicodeDecodeError`/`OSError` and the PostToolUse hook exits with a
traceback on every exec call while the file exists.

Repro: `bad.md` containing bytes `\x96\x97\x98 latin1 \x80` next to a
valid note, `BUNDLE_MEMORY_DIR` pointed at the dir, PostToolUse payload
on stdin -> `UnicodeDecodeError`, exit 1.

Identical defect was fixed in the sibling `memory-retrieval.py` in
audit R1; this hook was missed.

## Fix

Wrap `load_note` in the loop with try/except (OSError,
UnicodeDecodeError) and skip the bad note -- fail-open contract held.

## Verification

`tests/test_hook_memory_post_exec.py` (or nearest memory-hook test
file): unreadable note is skipped, valid notes still score, hook
exits 0.

## Answer

Fixed. `load_note(p)` is wrapped in try/except (OSError,
UnicodeDecodeError) inside the glob loop; an unreadable/non-UTF8 note
is skipped instead of crashing the hook. Repro now exits 0. Tests:
`test_hook_memory_post_exec.py` (3 tests: bad note skipped, valid
note still scores, no-match silent).
