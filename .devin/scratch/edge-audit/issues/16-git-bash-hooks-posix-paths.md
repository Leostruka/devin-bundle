# 16 -- Git Bash install renders hook commands with POSIX paths Windows python cannot open
- **Status**: open
- **Category**: user-experience
- **Severity**: P2
- **File**: install.sh:170-180, 380; scripts/render-user-hooks.py:36-42

## Evidence
On Git Bash (`MINGW*|MSYS*|CYGWIN*`), install.sh resolves `DEVIN_HOME` via `cygpath -u "$APPDATA"` (line 174), producing a POSIX path like `/c/Users/<name>/AppData/Roaming/devin`. The sed fallback (line 176) produces the same `/c/...` shape. That value is passed verbatim to `render-user-hooks.py` (line 380), which interpolates it into hook commands as `python "{home}/scripts/<name>.py"` (render line 42).

The Devin CLI on Windows is a native process: when it spawns `python "/c/Users/.../scripts/pre-exec-guard.py"`, the Windows python interpreter receives `/c/Users/...` as an argv path it cannot resolve (it is not a valid Win32 path; there is no `/c` root). Every rendered hook then fails to spawn. Because `pre-exec-guard` and `pre-write-guard` are registered with `"fail_closed": true` (hooks.v1.json:9, 19), exec/write tool calls are blocked outright on machines installed via Git Bash, and the installer reports success (`config.json hooks rendered`) with no validation that the paths are spawnable.

Note: `pythonw` is also used when present (render-user-hooks.py:27-28), same path problem.

## Recommendation
Convert `DEVIN_HOME` to Windows form before rendering on MSYS: `cygpath -w "$DEVIN_HOME"` (or `-m` for mixed `C:/...`), or have render-user-hooks.py normalize the incoming home via `os.path.abspath`/`cygpath` when it detects a `/x/` drive pattern. Add a post-render sanity check that `scripts/pre-exec-guard.py` exists at the rendered path.

## Tradeoffs
Merits: hooks actually fire on Git Bash installs; fail_closed guards stop bricking the agent. Demerits: config.json then contains Windows-style paths, which is correct anyway since the CLI is a Windows process.

## Verification
On Git Bash: `cygpath -u "$APPDATA"` yields `/c/...`; inspect `%APPDATA%\devin\config.json` `hooks` after `./install.sh` and observe `"command": "pythonw \"/c/Users/.../scripts/...\""`. Attempting `python "/c/Users/.../scripts/session-start.py"` in cmd.exe fails with `can't open file`.
