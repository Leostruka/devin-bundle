# computer-use — GUI automation (replicates Devin Cloud Computer Use)

Local tools for screen capture, mouse control, and keyboard input. Use when a
task needs visual verification of a desktop app or interaction with a UI that
has no API/CLI.

## Layout

| File | Purpose |
|---|---|
| `screenshot.py` | Capture screen/region/monitor to PNG, `--grid` overlay |
| `mouse.py` | move, click, scroll, drag, position |
| `type_text.py` | type literal text, single keys, hotkey chords |
| `requirements.txt` | `mss` (capture) + `pynput` (input) + `pillow` (grid overlay) |

Installed to `~/.config/devin/extensions/computer-use/` (Windows:
`%APPDATA%\devin\extensions\computer-use\`) by `install.sh` / `install.ps1`,
which also create an isolated `.venv/` there and install `requirements.txt`
into it. No system/user-site packages are touched.

## Interpreter

Always run the scripts with the extension's venv Python:

- POSIX: `~/.config/devin/extensions/computer-use/.venv/bin/python`
- Windows: `%APPDATA%\devin\extensions\computer-use\.venv\Scripts\python.exe`

If the venv is missing (install ran without Python), create it manually:

```bash
python3 -m venv <ext-dir>/.venv
<ext-dir>/.venv/bin/python -m pip install -r <ext-dir>/requirements.txt
```

## Contract

- Every script prints exactly one JSON object to stdout: `{"ok": true, ...}` or `{"ok": false, "error": "..."}`.
- Exit codes: `0` success, `1` runtime failure, `2` usage/dependency error.
- Coordinates are physical pixels, origin at the top-left of the primary monitor. On multi-monitor setups, monitor 0 = the combined virtual screen; negative coordinates are valid for secondary monitors.
- On Windows the scripts set per-monitor DPI awareness so screenshot pixels and mouse coordinates agree on scaled displays.
- Default `--out` goes to the OS temp dir (`%TEMP%`/`/tmp`) — screenshots are disposable. To keep one as project documentation/evidence, pass an explicit path under `.devin/` (e.g. `--out .devin/screenshots/login.png`), the conventional home for agent working artifacts.

## Commands

```bash
PY=~/.config/devin/extensions/computer-use/.venv/bin/python   # Windows: %APPDATA%\devin\extensions\computer-use\.venv\Scripts\python.exe

# --- screenshot.py ---
$PY screenshot.py --out shot.png                  # all monitors combined
$PY screenshot.py --grid --out shot.png           # + coordinate grid (labels = physical px)
$PY screenshot.py --grid 200 --out shot.png       # grid every 200 px
$PY screenshot.py --monitor 1 --out mon1.png      # specific monitor (1..N)
$PY screenshot.py --region 100,200,640,480 --out crop.png   # x,y,w,h crop

# --- mouse.py ---
$PY mouse.py position                    # {"ok":true,"x":...,"y":...}
$PY mouse.py move 500 300
$PY mouse.py click 500 300               # left click at (500,300), 50ms hold
$PY mouse.py click 500 300 --button right
$PY mouse.py click 500 300 --clicks 2    # double-click
$PY mouse.py click 500 300 --hold 150    # longer press for debounced UIs
$PY mouse.py scroll 500 300 --dy -3      # scroll up 3 steps (+dy = down)
$PY mouse.py drag 800 400 --from-x 500 --from-y 300 --duration 0.5

# --- type_text.py ---
$PY type_text.py "hello world"           # literal text
$PY type_text.py "user@example.com" --enter
$PY type_text.py --key enter             # single named key
$PY type_text.py --keys ctrl+c           # chord (modifiers + key)
$PY type_text.py --keys ctrl+shift+s
$PY type_text.py "slow" --delay 0.05     # 50 ms between chars
```

Key names: `ctrl`, `alt`, `shift`, `win`/`cmd`, `enter`, `esc`, `tab`, `space`,
`backspace`, `delete`, `insert`, `home`, `end`, `pageup`, `pagedown`,
`up`/`down`/`left`/`right`, `f1`–`f24`, `capslock`, `printscreen`, or any
single character.

## Agent workflow

1. `screenshot.py --grid --out shot.png` → `read` the PNG.
2. Read the target's (X, Y) **from the grid labels** — never estimate from the
   image proportions (see failure modes below).
3. `mouse.py click X Y` and/or `type_text.py`.
4. `screenshot.py` again to verify the result before continuing.

**Always use `--grid` when the next step is a click.** The image the agent
perceives is rescaled by the reader; coordinates estimated from the perceived
image are systematically off by the render scale (~20% on 1080p). The grid
labels are drawn on the physical pixels, so they read true regardless of how
the image is displayed.

## Failure modes

- **Wayland (Linux):** pynput keyboard/mouse control needs X11 or an XWayland
  session; screenshots may also fail. On pure Wayland, report the limitation
  instead of retrying.
- **macOS:** first run triggers macOS permission prompts (Screen Recording for
  capture, Accessibility for input). Grant them to the terminal app, then re-run.
- **Focused-window dependency:** typing and clicks go to whatever has focus —
  take a screenshot first if unsure which window is active.
- **"ok:true" but nothing happened:** the input was dispatched to the OS — the
  contract does not mean the UI changed. Check, in order: (a) aim — retake
  `screenshot.py --grid` and confirm the coordinate sits on the element;
  (b) focus — a click on a background window may only focus it, click again;
  (c) debounce — retry with `--hold 150`; (d) overlay — a transparent window or
  tooltip may be eating the event.
- **Coordinate space:** click coordinates are physical pixels. Values estimated
  from the perceived (rescaled) screenshot miss the target — use `--grid`.
- **Headless sessions** (SSH, CI): no display → scripts return `ok:false`.
  Do not retry.

## Safety

These scripts act on the real desktop with the user's permissions (Rule 13).
Confirm coordinates from a fresh screenshot before clicking; never chain
click+type blind. Input goes to the focused window — a mistargeted command can
type into the wrong app.
