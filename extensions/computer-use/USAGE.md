# computer-use — GUI automation (replicates Devin Cloud Computer Use)

Local tools for screen capture, mouse control, and keyboard input. Use when a
task needs visual verification of a desktop app or interaction with a UI that
has no API/CLI.

## Layout

| File | Purpose |
|---|---|
| `screenshot.py` | Capture screen/region/monitor to PNG, `--grid` overlay, `--hints` Vimium-style element badges + observation contract |
| `mouse.py` | move, click (incl. `--hint`, `--via`, `--verify`), scroll, drag, position — profile-driven motion |
| `type_text.py` | type literal text, single keys, hotkey chords — profile-driven cadence, `--hint`/`--via uia` set-value |
| `profile.py` | get/set the session action profile (`--set`, `--show`, interactive menu) |
| `cu_motion.py` | shared: profile state + bezier/minimum-jerk path + timing generators |
| `cu_hints.py` | shared: UIA element extraction (cached queries) + versioned hint sidecar + live re-location/Invoke/SetValue |
| `cu_actions.py` | shared: result contract (`status`, `dispatch.backend`, `timings_ms`) + `OwnedInputs` cleanup |
| `cu_capture.py` | shared: capture backend seam (`grab`, `monitors`, `apply_delta`) — `$CU_CAPTURE` selects backend (default `mss`) |
| `cu_browser.py` | shared: authorized-browser binding (loopback+pid, session+TTL) + `BrowserClient` — CDP (Chromium) or WebDriver BiDi (Firefox/Zen) via `websocket-client`; attach-only to a bound browser |
| `browser.py` | bound-browser CLI: `bind`/`status`/`eval`/`console`/`errors`/`requests`/`wait`/`cookies`/`storage`/`find`/`tabs`/`pin`/`navigate`/`events` — one-shot via JS collector + evaluate |
| `browser_events.py` | persistent events daemon (opt-in): holds the bound browser's ws open, buffers CDP/BiDi events — full-fidelity console/errors/network/dialogs/nav + dialog auto-policy + HAR-lite |
| `cu_terminal.py` | shared: terminal detection/binding (WT/conhost/mintty by window class) + UIA TextPattern & `CONOUT$` read paths + WinRT OCR for mintty + physical/`WriteConsoleInputW` control + command gate + PTY spawn sessions (pywinpty WinPTY backend) |
| `terminal.py` | terminal CLI: `bind`/`status`/`read`/`info`/`type`/`key`/`scroll`/`exec` (bound terminal) + `spawn`/`send-to`/`recv`/`close`/`kill`/`sessions` (own PTY via daemon) |
| `terminal_sessions.py` | persistent sessions daemon (opt-in): holds spawned PTYs across CLI invocations — loopback socket + pidfile, idle TTL |
| `probes/` | empirical research scripts from the terminal-control investigation (UIA/ConPTY/CONIN$/clipboard paths) — reference material, not shipped APIs |
| `cu_session.py` | shared: opt-in persistent worker over stdio pipes — recyclable, generation+session rotation, queue cancel |
| `cu_bench.py` | per-boundary latency harness (protocol 4.4) — `--runs N --out FILE`, JSON to stdout |
| `requirements.txt` | `mss` + `pynput` + `pillow` + `uiautomation`/`comtypes` (Windows) |

## Action profiles

Three profiles control how input is physically performed. Resolve order:
`--profile` flag > `$COMPUTER_USE_PROFILE` > session file
(`<temp>/devin-cu-profile.json`) > `fast`.

| Profile | Mouse | Typing |
|---|---|---|
| `fast` | teleport, zero delay (legacy default) | single instant `kb.type` |
| `smooth` | cinematic cubic-bezier arc, easeInOutCubic, ~90 fps | fixed 35 ms/char |
| `human` | multi-knot bezier + gaussian jitter + occasional overshoot, Fitts-law duration `MT = 0.08 + 0.16·log2(D/W+1)` | lognormal digram/trigram-context cadence — repeated letters faster, punctuation pauses, jittered click hold |

Motion generator: `--motion bezier` (default per profile) or `--motion minjerk`
(Flash–Hogan minimum-jerk path — straight, no jitter, no overshoot) on
`move`/`click`/`scroll`/`drag`. Paths and typing plans are reproducible with
`--seed N` (typing also honors `$CU_SEED`). Path playback uses absolute
deadlines — per-step sleep drift cannot accumulate.

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
- Action results carry `"status"` — `dispatched` (input sent, effect NOT verified), `verified`, `rejected` (pre-condition failed, zero input sent), `timeout`, `unknown`, `cancelled`. `ok:true` never means task success.
- `dispatch.backend` records the transport used: `physical` (pynput) or `uia` (semantic pattern). `dispatch.uia_fallback` names the typed reason when a `uia` attempt fell back (`stale`, `no_pattern`, `readonly`, `timeout`…).
- `timings_ms` reports measured wall-clock ms (`move`, `dispatch`, `total`); `secs` is the *planned* path/cadence duration — they are different things.
- `screenshot.py` output includes `origin_px` (image top-left in desktop space) and `captured_at`; with `--hints` also `session_id`, `observation_id`, `generation`, `window`, `truncated`.
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
$PY mouse.py click --hint as --via uia   # semantic Invoke only (reject, no fallback)
$PY mouse.py click --hint as --verify    # report postcondition.target_present
$PY mouse.py click 500 300 --motion minjerk   # minimum-jerk path
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
$PY type_text.py "text" --hint as        # target element; UIA SetValue when available
$PY type_text.py "text" --hint as --via uia    # SetValue only, reject on failure
$PY type_text.py "x" --profile human --seed 7  # reproducible cadence
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
(buttons, edits, links, checkboxes, menu/tab/list items…, cached one-shot
query) and draws Vimium-style letter badges at each element's corner. A
versioned sidecar (`<temp>/devin-cu-hints.json`) maps hint →
`{x, y, name, type, bounds, hwnd, enabled}` plus `session_id`, `generation`,
`window` binding and `created_at`. `click --hint` / `--hint` typing resolve
through it and **reject** — with zero input dispatched — when the hint is
unknown, expired (default TTL 120 s, `$CU_HINT_TTL`), from another session,
or its window no longer exists. A grid fallback invalidates the sidecar, so
stale hints can never resolve.
Hint ids alone are ambiguous across observations — pass `--gen <generation>`
(from the same `--hints` output) to pin the observation: after a newer
snapshot, the old hint rejects as `stale_generation`.
Hints are **targeting only** — they do not identify images, canvas content or
any non-UIA surface; use plain `screenshot.py` for visual checks.

With `--hint`, `--via auto` (default) re-locates the element live and uses its
UIA `Invoke`/`Value` pattern when supported, falling back to physical input;
`--via physical` skips UIA; `--via uia` rejects instead of falling back.
Semantic actions act on the element itself — they do not exercise the same
handlers as a physical click; keep `physical` when testing real input paths.

`--via browser` (click/type) requires the element's window to be an
**explicitly bound** browser (`cu_browser.bind`); unbound or foreign-pid
windows reject as `browser_no_binding`/`browser_foreign_process` with zero
dispatch. DOM dispatch is gated by an actionability probe
(`elementsFromPoint` stack): covered targets wait briefly then reject as
`browser_actionable_covered`; disabled/zero-size/canvas reject immediately
(`browser_actionable_*`). In `auto` mode a canvas hit declares
`dispatch.dom_fallback` and continues through UIA/physical — DOM never
pretends to click canvas pixels. CDP speaks to Chromium; Gecko (Firefox/Zen)
goes over WebDriver BiDi — nested-context eval is BiDi-only, CDP rejects
foreign contexts rather than evaluating in the wrong frame.

If UIA is unavailable, times out (>6 s), or finds no elements (non-Windows,
unusual apps), `--hints` falls back to the `--grid 100` overlay and reports
`"hints": null, "fallback": "grid"`. Set `CU_NO_UIA=1` to force the fallback.
Electron apps only expose their DOM to UIA with `--force-renderer-accessibility`.

## Bound-browser commands (`browser.py`)

Browser observation + control against a browser explicitly bound for this
session. Nothing is launched or auto-attached — bind first:

```bash
# launch your own Chromium with remote debugging, e.g.
#   chrome --remote-debugging-port=9222   (loopback only)
$PY browser.py bind --endpoint http://127.0.0.1:9222 --pid <chrome-pid>
$PY browser.py status                     # bound? reachable? dialect?
$PY browser.py unbind
```

One-shot commands (each opens the ws, acts, closes):

```bash
$PY browser.py eval "document.title" --boundaries   # wrap output as untrusted
$PY browser.py navigate https://example.com
$PY browser.py console [--clear] [--substr err]     # JS collector buffer
$PY browser.py errors  [--clear]
$PY browser.py requests [--clear] [--substr api]    # fetch/XHR only
$PY browser.py collect                    # inject collector before traffic
$PY browser.py wait --selector "#app" | --text Hi | --url "**/dash" | --fn "window.ready===true" [--state hidden] [--timeout 10]
$PY browser.py cookies
$PY browser.py storage local            # all entries | get K | set K V | remove K | keys | clear
$PY browser.py find role button --name Submit   # role|text|label|placeholder|alt|testid|title
$PY browser.py tabs
$PY browser.py pin <targetId>           # restrict to one tab; `pin off` clears
```

The collector wraps `console.*`, `window.onerror`/`unhandledrejection` and
`fetch`/`XHR` into bounded `window.__cu_*` buffers — installed as a preload
script so it survives navigation, and auto-installed on first
`console`/`errors`/`requests` call. Limits: app-level only — subresources,
redirects, WS frames and pre-injection events need the events daemon.

`--if-changed`/`--diff` on `screenshot.py` skip unchanged captures in verify
loops (`--threshold 0.01` tolerates ≤1% pixel drift).

## Events daemon (`browser.py events`)

For full-fidelity streams, spawn the opt-in daemon — it holds the bound
browser's ws open and buffers real protocol events:

```bash
$PY browser.py events start               # detached, loopback socket + pidfile
$PY browser.py events drain               # all buckets, clears
$PY browser.py events console|errors|requests|nav|dialogs
$PY browser.py events requests            # Network.*: subresources too
$PY browser.py events har out.json        # HAR-lite export of request log
$PY browser.py events tabs | pin <id>
$PY browser.py events dialogs             # pending confirm/prompt
$PY browser.py events respond accept|dismiss
$PY browser.py events status | stop
```

CDP path enables `Network`/`Runtime`/`Log`/`Page`; BiDi subscribes to
`log.entryAdded`, `network.*`, `browsingContext.userPromptOpened`,
`browsingContext.navigationStarted`/`load`. `alert`/`beforeunload` dialogs
are auto-accepted; `confirm`/`prompt` stay pending until `respond`.
Idle TTL 600 s (`$CU_BEVENTS_IDLE`); the pidfile lives in the OS temp dir.

**When UIA yields nothing, always use `--grid` for clicks.** The image the
agent perceives is rescaled by the reader; coordinates estimated from the
perceived image are systematically off by the render scale (~20% on 1080p).
The grid labels are drawn on the physical pixels, so they read true
regardless of how the image is displayed.

## Terminal control (`terminal.py`)

Two modes. **Bound**: read/control an existing terminal window (same
bind+session+TTL contract as `browser.py`). **Spawn**: own a PTY — never
touches user terminals.

```bash
$PY terminal.py bind --hwnd 460176        # or --pid <pid>
$PY terminal.py status                    # bound? mode? window info
$PY terminal.py read [--tail 20|--find x] # scrollback, UNTRUSTED-wrapped
$PY terminal.py info                      # dims/cursor/mode
$PY terminal.py type "echo hi"            # physical typing (focus first)
$PY terminal.py key enter|ctrl+c|...
$PY terminal.py scroll up|down [N]
$PY terminal.py exec "dir" --timeout 10   # sentinel-based completion + exit code
$PY terminal.py unbind
```

Mode detection by window class: `CASCADIA_*` → Windows Terminal (UIA
`TextPattern` full scrollback), `ConsoleWindowClass` → conhost (`CONOUT$`
buffer + `WriteConsoleInputW` injection), `mintty` → Git Bash (WinRT
`Windows.Media.Ocr` on the window screenshot — probabilistic text, not
guaranteed; falls back to image-only when winrt is absent or fails).
Control on mintty stays physical (focus + type + verify via OCR reread).

`exec` appends a `CU_EXIT_<tag>` sentinel, waits for it (or idle), strips
echo+prompt, caps output at 16K chars (spill → temp file). Command gate:
`rm|del|kill|format|shutdown|taskkill|Remove-Item|...` → denied;
`curl|wget|eval|iex|sudo|...` → `--confirm` required. Input-needed states
(`[y/N]`, `Password:`, `(END)`) reported as `state:input_needed` — never
auto-answer passwords.

Spawn mode runs through the sessions daemon (auto-started):

```bash
$PY terminal.py spawn --shell cmd|powershell|pwsh|bash|wsl [--cols --rows]
$PY terminal.py send-to <sid> "echo hi\n"   # raw PTY write
$PY terminal.py recv <sid> [--tail N|--wait REGEX --timeout S]
$PY terminal.py sessions list|status
$PY terminal.py close <sid> | kill <sid>
$PY terminal.py sessions stop
```

`recv` flags `alt_buffer:true` on fullscreen apps (vim/htop) — detach, don't
wait for completion. Daemon idle TTL 900 s (`$CU_TSDAEMON_IDLE`); pidfile in
OS temp. Known limits: ConPTY backend fails on some builds (WinPTY used —
see plan), mintty read is OCR-based (image fallback if winrt missing),
`wt send-input` does not exist.

## Failure modes

- **Wayland (Linux):** pynput keyboard/mouse control needs X11 or an XWayland
  session; screenshots may also fail. On pure Wayland, report the limitation
  instead of retrying.
- **macOS:** first run triggers macOS permission prompts (Screen Recording for
  capture, Accessibility for input). Grant them to the terminal app, then re-run.
- **Focused-window dependency:** typing and clicks go to whatever has focus —
  take a screenshot first if unsure which window is active.
- **"status: dispatched" but nothing happened:** the input was dispatched to
  the OS — the contract does not mean the UI changed. Check, in order: (a) aim — retake
  `screenshot.py --grid` and confirm the coordinate sits on the element;
  (b) focus — a click on a background window may only focus it, click again;
  (c) debounce — retry with `--hold 150`; (d) overlay — a transparent window or
  tooltip may be eating the event.
- **Coordinate space:** click coordinates are physical pixels. Values estimated
  from the perceived (rescaled) screenshot miss the target — use `--hints` or
  `--grid`.
- **Stale hints:** hint ids refer to the last `--hints` capture only — re-run
  `screenshot.py --hints` after any UI change before `click --hint`. Stale or
  expired hints are rejected before any input is dispatched (`"rejected:
  expired|window_gone|session|schema"`); a grid fallback deletes the sidecar.
- **Headless sessions** (SSH, CI): no display → scripts return `ok:false`.
  Do not retry.

## Safety

These scripts act on the real desktop with the user's permissions (Rule 13).
Confirm coordinates from a fresh screenshot before clicking; never chain
click+type blind. Input goes to the focused window — a mistargeted command can
type into the wrong app.
