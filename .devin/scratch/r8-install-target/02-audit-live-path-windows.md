# R8-02: audit.py [15] prefers .config/devin over %APPDATA% on Windows

**Severity:** P2 (masks real drift)
**File:** audit.py:498-505

**Defect:** live-path detection checks `~/.config/devin` FIRST, then
`%APPDATA%\devin`. On Windows the CLI reads %APPDATA%; when the shadow
.config dir also exists (written by install.sh pre-fix), the sync
checks validate the shadow and report "live=bundle" while the real
CLI config drifts.

**Evidence:** post-install audits passed 0 warnings while
%APPDATA%\devin\skills\{brag,agentic-rag} were stale.

**Fix:** on os.name == 'nt' prefer %APPDATA%\devin (fall back to
.config only when %APPDATA% absent); emit a warning when BOTH exist
so the shadow copy is visible.
