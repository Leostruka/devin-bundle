# 35 -- AGENTS.md case-variant duplication: install-time dedup only, CLI bug unfixed

- **Status**: open
- **Category**: devin-cli-limitations
- **Severity**: P3
- **File**: install.ps1:369-405

## Evidence

On case-insensitive filesystems the Devin CLI can list `AGENTS.md` twice (Windows/WSL /mnt/c, default macOS). `install.ps1` works around it: `Test-CaseSensitive` probes the FS (369-380), removes a separate lowercase `agents.md` on case-sensitive FSs (390-401), and on case-insensitive FSs can only warn "Devin CLI may list AGENTS.md twice (known bug, not fixable here)" (405). The installed-rules duplicate listing persists for every Windows user; the dedup step also runs at install only, so a project that later gains `agents.md` is never rechecked.

## Recommendation

Keep the install dedup; additionally have `audit.py` or `devin rules list` post-install verification detect the duplicate-listing symptom and document the upstream bug ID so the workaround can be retired when fixed.

## Tradeoffs

- Merits: deterministic at install, cheap probe, no runtime cost; removing a foreign `agents.md` prevents real double-injection of rules into context.
- Demerits: warn-only on the most common platform (Windows) means the known bug ships to every Windows install; deleting `agents.md` could remove a legitimately different file a project intended; no periodic re-check.
- Better contorno: none inside the bundle while the CLI reads both casings; the real fix is upstream. A symlink/normalization trick would break other tools.

## Verification

`install.ps1:405` warn path; run `devin rules list` on a case-insensitive FS with an `agents.md` present to observe double listing.
