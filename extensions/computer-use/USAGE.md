# computer-use — GUI automation (replicates Devin Cloud Computer Use)

Local tools for screen capture, mouse control, and keyboard input. Use when a
task needs visual verification of a desktop app or interaction with a UI that
has no API/CLI.

## Layout

| File | Purpose |
|---|---|
| `screenshot.py` | Capture screen/region/monitor to PNG, `--grid` overlay, `--hints` Vimium-style element badges |
| `mouse.py` | move, click (incl. `--hint`), scroll, drag, position — profile-driven motion |
| `type_text.py` | type literal text, single keys, hotkey chords — profile-driven cadence |
| `profile.py` | get/set the session action profile (`--set`, `--show`, interactive menu) |
| `cu_motion.py` | shared: profile state + bezier/Fitts path + timing generators |
| `cu_hints.py` | shared: UIA element extraction + hint sidecar |
| `requirements.txt` | `mss` + `pynput` + `pillow` + `uiautomation`/`comtypes` (Windows) |

## Action profiles

Three profiles control how input is physically performed. Resolve order:
`--profile` flag > `$COMPUTER_USE_PROFILE` > session file
(`<temp>/devin-cu-profile.json`) > `fast`.

| Profile | Mouse | Typing |
|---|---|---|
| `fast` | teleport, zero delay (legacy default) | single instant `kb.type` |
| `smooth` | cinematic cubic-bezier arc, easeInOutCubic, ~90 fps | fixed 35 ms/char |
| `human` | multi-knot bezier + gaussian jitter + occasional overshoot, Fitts-law duration `MT = 0.08 + 0.16·log2(D/W+1)` | `gauss(90ms,30ms)`/char, double-letter speedup, ~3% thinking pauses, jittered click hold |

Agents: at session start, ask the user which profile to use, then run
`profile.py --set <name>`. Humans in a real terminal can run `profile.py`
bare for an interactive menu (prompts go to stderr; stdout stays JSON).

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
- Default `--out` goes to the OS temp dir (`%TEMP%`/`/tmp`) — screenshots are disposable. **Do not pass `--out` at all during normal work**; let shots land in temp. Only write elsewhere when the user explicitly asks to keep a shot (documentation/evidence), to the path they choose.
- **Cleanup:** temp shots are the agent's working files — delete the ones you created when the task ends (`screenshot-<ts>.png` etc.). Never leave them in the project root or `.devin/`.

## Commands

```bash
PY=~/.config/devin/extensions/computer-use/.venv/bin/python   # Windows: %APPDATA%\devin\extensions\computer-use\.venv\Scripts\python.exe

# --- profile.py ---
$PY profile.py --set human             # persist session profile
$PY profile.py --show                  # effective profile + source
$PY profile.py                         # interactive menu (terminal use)

# --- screenshot.py --- (all write to the OS temp dir unless --out is given)
$PY screenshot.py                                 # all monitors combined → temp
$PY screenshot.py --hints                         # Vimium badges on UI elements
$PY screenshot.py --hints --window all            # all windows, not just focused
$PY screenshot.py --grid                          # + coordinate grid (labels = physical px)
$PY screenshot.py --grid 200                      # grid every 200 px
$PY screenshot.py --monitor 1                     # specific monitor (1..N)
$PY screenshot.py --region 100,200,640,480        # x,y,w,h crop
$PY screenshot.py --grid --out /keep/here.png     # only when asked to keep the shot

# --- mouse.py ---
$PY mouse.py position                    # {"ok":true,"x":...,"y":...}
$PY mouse.py move 500 300
$PY mouse.py click 500 300               # left click at (500,300)
$PY mouse.py click --hint as             # click element from screenshot --hints
$PY mouse.py click 500 300 --button right
$PY mouse.py click 500 300 --clicks 2    # double-click
$PY mouse.py click 500 300 --hold 150    # explicit hold wins over profile jitter
$PY mouse.py scroll 500 300 --dy -3      # scroll up 3 steps (+dy = down)
$PY mouse.py drag 800 400 --from-x 500 --from-y 300 --duration 0.5
$PY mouse.py move 500 300 --profile smooth   # per-call profile override
$PY mouse.py click 500 300 --dry-run     # compute path, dispatch no input

# --- type_text.py ---
$PY type_text.py "hello world"           # literal text (profile-paced)
$PY type_text.py "user@example.com" --enter
$PY type_text.py --key enter             # single named key
$PY type_text.py --keys ctrl+c           # chord (modifiers + key)
$PY type_text.py --keys ctrl+shift+s
$PY type_text.py "slow" --delay 0.05     # fixed 50 ms/char (overrides profile)
$PY type_text.py "x" --profile human --dry-run   # timing plan, no input
```

Key names: `ctrl`, `alt`, `shift`, `win`/`cmd`, `enter`, `esc`, `tab`, `space`,
`backspace`, `delete`, `insert`, `home`, `end`, `pageup`, `pagedown`,
`up`/`down`/`left`/`right`, `f1`–`f24`, `capslock`, `printscreen`, or any
single character.

## Agent workflow

1. `screenshot.py --hints` → `read` the PNG **and** the JSON `hints` array —
   each entry has `{id, x, y, name, type}`: pick the element by `name`/`type`
   straight from stdout, no pixel estimation needed.
2. `mouse.py click --hint <id>` (or `click X Y` with the entry's coords) and/or
   `type_text.py`.
3. `screenshot.py` again to verify the result before continuing.

`--hints` enumerates real interactive elements via Windows UI Automation
(buttons, edits, links, checkboxes, menu/tab/list items…) and draws
Vimium-style letter badges at each element's corner. A sidecar file
(`<temp>/devin-cu-hints.json`) maps hint → exact center for `click --hint`.
Hints are **targeting only** — they do not identify images, canvas content or
any non-UIA surface; use plain `screenshot.py` for visual checks.

If UIA is unavailable, times out (>6 s), or finds no elements (non-Windows,
unusual apps), `--hints` falls back to the `--grid 100` overlay and reports
`"hints": null, "fallback": "grid"`. Set `CU_NO_UIA=1` to force the fallback.
Electron apps only expose their DOM to UIA with `--force-renderer-accessibility`.

**When UIA yields nothing, always use `--grid` for clicks.** The image the
agent perceives is rescaled by the reader; coordinates estimated from the
perceived image are systematically off by the render scale (~20% on 1080p).
The grid labels are drawn on the physical pixels, so they read true
regardless of how the image is displayed.

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
  from the perceived (rescaled) screenshot miss the target — use `--hints` or
  `--grid`.
- **Stale hints:** hint ids refer to the last `--hints` capture only — re-run
  `screenshot.py --hints` after any UI change before `click --hint`.
- **Headless sessions** (SSH, CI): no display → scripts return `ok:false`.
  Do not retry.

## Safety

These scripts act on the real desktop with the user's permissions (Rule 13).
Confirm coordinates from a fresh screenshot before clicking; never chain
click+type blind. Input goes to the focused window — a mistargeted command can
type into the wrong app.
