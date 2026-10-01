---
name: computer-use
description: Use when you need to see or control the local screen (screenshots, screen recording with video + contact sheet for catching transient bugs/animations, mouse clicks/movement, typing text and hotkeys) or to read/control terminals (Windows Terminal, conhost, mintty, spawned PTYs). GUI automation for desktop apps and browsers, replicating Devin Cloud Computer Use in the CLI.
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

At session start, ask the user which action profile to use
(`ask_user_question`: `fast` / `smooth` / `human`), then persist it:

```bash
PY profile.py --set human              # writes session file in OS temp dir
```

Always invoke via the extension's isolated venv Python:

- Windows: `%APPDATA%\devin\extensions\computer-use\.venv\Scripts\python.exe`
- POSIX: `~/.config/devin/extensions/computer-use/.venv/bin/python`

```bash
PY screenshot.py --hints               # Vimium-style badges on real UI elements
PY screenshot.py --grid                # fallback when UIA has no elements
PY mouse.py click --hint as            # click element center by hint id
PY mouse.py click X Y                  # or click physical pixel directly
PY type_text.py "text" | --keys ctrl+c # type / hotkey
PY record.py --seconds 5               # screen video + contact-sheet PNG
PY terminal.py bind --hwnd <n>          # read/control an existing terminal
PY terminal.py spawn --shell cmd        # or own a PTY session (daemon)
PY terminal.py link <src> <dst>         # pipe session A output into B input
PY terminal.py links | unlink <id>      # inspect / stop a link
PY browser.py bind --endpoint <url> --pid <p>  # browser via CDP/BiDi
# Android: envs/<id>.json {"provider":"adb","serial":"..."} then:
PY screenshot.py --env <id> --hints     # uiautomator tree -> hint badges
PY mouse.py click --hint as --env <id>  # tap element center via adb
PY terminal.py exec "ls /sdcard" --env <id>  # adb shell
```

Terminal/browser details (read paths, send/exec/recv, events daemon) are in
`USAGE.md` — same directory.

Workflow: `screenshot.py --hints` → pick the target by `name`/`type` from the
JSON (or the badge letters in the PNG) → `mouse.py click --hint <id>` →
re-screenshot to verify. For visual checks (images, canvas, rendered content)
use plain `screenshot.py`; hints only cover interactive elements.

Recording: `record.py` writes a video file (mp4/webm via ffmpeg, animated
webp/gif via Pillow fallback) **plus a contact-sheet PNG**. Read the sheet
with the `read` tool to see what happened; video can't be viewed directly.
Use for transient bugs, animations, flicker, and anything a single
screenshot misses.

Screenshots are disposable: keep the default temp path, and delete the shots
you created when the task ends. Only write `--out` elsewhere if the user asks
to keep one.

Isolated environments: any CLI takes `--env <env_id>` to act inside an
approved QEMU/container guest instead of the host — lifecycle via
`env.py` (doctor/create/start/stop/restart/reset; TTY consent required).
Details and limits: `USAGE.md` → "Isolated environments".

If the venv is missing, run the bundle installer (`install.ps1`/`install.sh`)
or create it per `USAGE.md`.
