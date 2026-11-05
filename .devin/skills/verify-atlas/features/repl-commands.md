# REPL commands

## Sub-features
Footer `#repl` input executes: help, cd, ls, cat, open, grep, doctor, install, version, pwd, history, clear, :q + section names. Up/down history, Tab completion.

## How to get to it (user POV)
Type anywhere - focus lands in the REPL. Output prints to `#repl-out`, path shows in `#repl-path`.

## Driving it with curl + headless Edge
- Command table: `curl -s http://localhost:8737/app.js | grep -o '"help","cd","ls","cat","open","grep","doctor","install","version","pwd","history","clear",":q"'` -> command list shipped.
- `go()`/`curSec` wiring: grep app.js for `repl-path` update inside the section-switch function.
- Visual: screenshot after virtual-time budget shows prompt `leostruka@devin-bundle` + path.

## Gotchas
- Commands operate on the embedded DATA payload (skills/agents/docs), not the filesystem - `cat <skill>` works only for real skill names; an empty answer for a valid skill means DATA payload truncation.
- `:q` clears output, does not close anything - do not expect the tab to die.
