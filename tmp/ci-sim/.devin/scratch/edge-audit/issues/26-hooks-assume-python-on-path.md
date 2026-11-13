# 26 -- Hooks assume `python` on PATH; POSIX installs with only python3 break or lock the agent
- **Status**: resolved
- **Category**: user-experience
- **Severity**: P2
- **File**: hooks.v1.json (all entries use `python scripts/...`), scripts/render-user-hooks.py:23-29

## Evidence
Every hook command in hooks.v1.json is `python scripts/<name>.py` (e.g. PreToolUse pre-exec-guard, post-exec, SessionStart session-start, Stop stop-guard). `render-user-hooks.py::hook_python()` returns `'pythonw'` on Windows when available, otherwise `'python'` for all platforms including Linux/macOS (line 29). On stock macOS and many minimal Linux/WSL images only `python3` exists; `python` is not on PATH.

Impact is worse than a warning: `pre-exec-guard` and `pre-write-guard` are registered with `"fail_closed": true` (hooks.v1.json:9, 19). If the hook command cannot spawn, exec/write tool calls fail closed, effectively disabling the agent's core tools. The installer detects this only partially: install.sh:379-387 warns "python not found" during hook render but uses `command -v python` (not python3), so on a python3-only system it silently skips hook rendering while install.sh's own venv step would have succeeded via python3 (lines 546-548). The user ends with no rendered hooks and just one warning line, or worse with rendered hooks pointing at a nonexistent interpreter.

## Recommendation
Have `hook_python()` probe `python`, then `python3`, and emit whichever exists; make both installers perform the same probe and warn loudly (or set the resolved interpreter into the rendered commands) when neither exists. Consider whether fail_closed guards should degrade to a warning when the interpreter itself is missing.

## Tradeoffs
Merits: hooks work on python3-only systems; no silent skip. Demerits: interpreter resolution becomes environment-dependent at render time rather than fixed.

## Verification
On a system without `python`: `command -v python` fails while `command -v python3` succeeds; `python scripts/pre-exec-guard.py` would spawn-fail and, with fail_closed, block the exec tool.

## Answer
Fixed in scripts/render-user-hooks.py: `hook_python()` now returns
`sys.executable` (the interpreter the installer itself resolved and ran the
renderer with), preferring `pythonw.exe` next to it on Windows. Rendered hook
commands therefore embed a known-good absolute interpreter path instead of
the bare `python` spelling, so python3-only POSIX systems keep working.
Installers already probe python/python3/py before invoking the renderer
(install.sh:94-99, install.ps1:644), so sys.executable is always a working
interpreter at render time.
