# 03 -- skill scan scripts: unreadable file aborts whole scan

- **Status**: resolved
- **Severity**: P3
- **Files**: `skills/obsidian-workflow/scripts/audit.py`,
  `skills/obsidian-workflow/scripts/scan_secrets.py`,
  `skills/obsidian-workflow/scripts/validate_links.py`,
  `skills/memory-management/scripts/audit-memory.py`

## Evidence

All four iterate vault/memory files calling
`open(fp, encoding="utf-8")` unguarded inside the loop. Obsidian
vaults routinely contain non-UTF8 notes (exports, editor quirks) -- a
single one raises `UnicodeDecodeError` and the entire audit/scan dies,
reporting nothing.

## Fix

Open with `errors="replace"` (content validators can tolerate
replacement chars) or skip the unreadable file with a warning line --
match each script's reporting style.

## Verification

Feed a dir containing one cp1252 `.md` plus valid notes; scan
completes and reports valid findings.

## Answer

Fixed. obsidian-workflow audit.py (3 open sites), scan_secrets.py and
validate_links.py now open with errors='replace' so one non-UTF8 note
cannot abort the scan. audit-memory.py wraps per-page open in
try/except OSError + errors='replace'. Test: scan_secrets.scan_file
on a cp1252 file returns findings without raising.
