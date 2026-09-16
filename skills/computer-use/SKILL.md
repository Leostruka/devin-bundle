---
name: computer-use
description: Use when you need to see or control the local screen — screenshots, mouse clicks/movement, typing text and hotkeys. GUI automation for desktop apps and browsers, replicating Devin Cloud Computer Use in the CLI.
triggers: [user, model]
---

# Computer Use

Local GUI automation. The scripts live in the `computer-use` extension, not in
this skill — this file is only the router pointer.

## Where it is

- Bundle source: `extensions/computer-use/`
- Installed: `%APPDATA%\devin\extensions\computer-use\` (Windows) or
  `~/.config/devin/extensions/computer-use/` (POSIX)
- **Full docs: `USAGE.md` inside that directory** — read it first.

## Quick start

Always invoke via the extension's isolated venv Python:

- Windows: `%APPDATA%\devin\extensions\computer-use\.venv\Scripts\python.exe`
- POSIX: `~/.config/devin/extensions/computer-use/.venv/bin/python`

```bash
PY screenshot.py --grid --out shot.png   # capture + coordinate grid
PY mouse.py click X Y                    # click physical pixel (X,Y)
PY type_text.py "text" | --keys ctrl+c   # type / hotkey
```

Workflow: `screenshot.py --grid` → `read` the PNG → pick (X,Y) from the grid
labels (they are physical pixels — do NOT estimate from image proportions) →
act → re-screenshot to verify.

If the venv is missing, run the bundle installer (`install.ps1`/`install.sh`)
or create it per `USAGE.md`.
