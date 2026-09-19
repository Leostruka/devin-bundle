# Plan: `cu_terminal` — terminal read/control for computer-use

Status: probing complete, design validated. Implementation pending approval.

## Empirical capability matrix (this machine, Win11 25H2 b26200, WT 1.24)

| Surface | Read | Write/Control | Verdict |
|---|---|---|---|
| **Windows Terminal** (`CASCADIA_*`, `TermControl`) | UIA `TextPattern` → **full scrollback** (868K chars proven) | Physical input (focus+type+keys) ✅; `TextRange.Select()` ✅ | Primary: UIA read + physical control |
| **conhost** (`ConsoleWindowClass`: cmd, powershell.exe, wsl bash in console) | `AttachConsole`+`CONOUT$` → **full buffer** (120×9001 scrollback); UIA "Text Area" Document → visible-ish only | **`WriteConsoleInputW` → 100% reliable** (full cmd exec proven) | Strongest: API read+write |
| **ConPTY-hosted shell** (WT tabs: `OpenConsole`/`PseudoConsoleWindow`) | `AttachConsole`+`CONOUT$` → visible buffer only (94×50) | `WriteConsoleInputW` → **flaky** (chars dropped) | Read best-effort; control via physical |
| **mintty** (Git Bash) | **Nothing programmatic** — screenshot/OCR only | Physical typing ✅; clipboard copy unreliable | Pixels-only |
| **wt.exe CLI** | structural verbs only (`new-tab`, `focus-tab`…) | **`send-input` does not exist** — rejected upstream (PR #20106) | Dead end, confirmed |
| **Own PTY spawn (OS `CreatePseudoConsole`)** | pipe → **broken on this build**: child attaches (120×30 proven) but output relay stalls after ~115 init bytes | input write lands | Do not use OS ConPTY |
| **Own PTY spawn (winpty/pywinpty `Backend.WinPTY`)** | pipe → **works fully** (banner+echo+prompt roundtrip) | write works | Use pywinpty for spawn mode |
| **WSL bash** | `wsl.exe` stdio pipes (deterministic) + `WSL_UTF8=1` | stdin pipe; `wsl tmux send-keys` if tmux | Spawn-mode variant |
| **WezTerm** | `wezterm cli get-text` | `cli send-text` | Not installed |
| **Alacritty** | none | `alacritty msg` — no send-text | Not installed |
| **VS Code terminal** | accessible buffer (SR view); ConPTY underneath → AttachConsole applies | in-process ext API only | Out of scope v1 |

## Design — `extensions/computer-use/cu_terminal.py` + `terminal.py` CLI

Two modes, one auth model (explicit `bind`, same as `cu_browser`).

### Mode A — observe/control existing terminal (`bind`)

Detection by window class / process tree:

1. `CASCADIA_HOSTING_WINDOW_CLASS` / `TermControl` present → **WT path**
   - read: UIA `TextPattern.DocumentRange.GetText(-1)` → full scrollback, `tail`, `find`, `cursor-row`
   - detail: `AttachConsole(shell_pid)`+`CONOUT$` → dims/cursor/attrs (guard `SetConsoleCtrlHandler(NULL,TRUE)`, `FreeConsole` immediately)
   - control: `SetForegroundWindow`(AttachThreadInput) + pynput type/key/scroll; verify by UIA re-read after each action
2. `ConsoleWindowClass` → **conhost path**
   - read: `AttachConsole`+`CONOUT$` `ReadConsoleOutputW` → full buffer incl. scrollback, cursor, attrs
   - control: `WriteConsoleInputW` (CONIN$) → deterministic keystrokes/commands; fallback physical input
   - shell resolution: window pid IS the shell client pid (36632=cmd proven)
3. `mintty` → **pixel path**
   - read: `screenshot.py --region` (existing); optional OCR later
   - control: physical only
4. unknown → fail closed

### Mode B — spawn controlled session (`spawn`)

`pywinpty` (`Backend.WinPTY` — ConPTY backend broken on this build) → `read`/`write`/`resize`/`wait`/`terminate`. Deterministic exec: `send-keys "cmd"`, wait-for marker/regex with timeout. Optional `wsl.exe`+pipes variant for bash. NOT a visible window (headless); a `wt new-tab`+marker variant for visible spawn is phase-2.

### CLI surface (`terminal.py`)

```
terminal.py bind --hwnd N|--pid P [--mode auto|wt|conhost|mintty] → session token+TTL
terminal.py status | read [--tail N | --find X | --line N] | info (dims/cursor/shell)
terminal.py type "text" | key enter|ctrl+c|... | scroll up|down [N]
terminal.py spawn --shell cmd|pwsh|powershell|bash|wsl [--cols --rows] → session
terminal.py send --session S "text" [--wait REGEX --timeout S] [--bg] [--confirm]
terminal.py recv --session S [--tail N] | close --session S | kill --session S
```

Output wrapped `--- BEGIN UNTRUSTED TERMINAL OUTPUT ---` … `--- END ---` (Rule 19-style boundary, same as browser eval).

### Safety

- bind validates hwnd belongs to pid + class whitelist; session token+TTL (reuse `cu_browser` binding model)
- `AttachConsole` only inside try/finally `FreeConsole`; `SetConsoleCtrlHandler(NULL,TRUE)` while attached
- no `GenerateConsoleCtrlEvent` (CTRL_C hits whole group); ctrl+c goes through input path only
- `type`/`key` require bound window focused first; verify-write loop (re-read, compare)
- clipboard never touched silently (mintty select-copy is best-effort, opt-in flag)
- OS `CreatePseudoConsole` spawn path gated behind `--pty os` flag, default `winpty`

## Test plan (RED first, fake seams)

- `tests/test_cu_terminal_detect.py` — class→mode detection table (fake hwnd/pid info)
- `tests/test_cu_terminal_uia.py` — fake UIA elements/TextPattern (comtypes seam like `cu_load`)
- `tests/test_cu_terminal_conhost.py` — fake kernel32 (AttachConsole/ReadConsoleOutput/WriteConsoleInput call log)
- `tests/test_cu_terminal_spawn.py` — fake pywinpty PTY (reader thread, marker wait, resize, terminate)
- `tests/test_cu_terminal_cli.py` — argv dispatch → ops (FakeClient, pattern from `test_cu_browser_cli`)
- `tests/test_cu_terminal_bind.py` — pid/hwnd mismatch reject, TTL expiry, foreign-class reject
- live probes stay out of unit suite — keep as `extensions/computer-use/probes/` manual scripts (Windows-only, gated `pytest.mark.skipif` if added at all)

## Deps

- `pywinpty` (compiled wheel, MIT) into cu venv `requirements.txt` — spawn mode only; lazily imported.
- UIA/conhost paths: existing `comtypes` + ctypes — zero new deps.

## Docs/sync

- `extensions/computer-use/USAGE.md` — terminal section (modes, per-surface capability table, caveats)
- `skills/computer-use/SKILL.md` — pointer line only if needed (thin router rule)
- manifest/audit: extensions not hash-tracked; SKILL-TIERS unchanged

## Extracted from `run_in_terminal` (microsoft/vscode `chatAgentTools`, verified source)

The Copilot terminal tool lives in **vscode core**, not copilot-chat — `src/vs/workbench/contrib/terminalContrib/chatAgentTools/`. Transferable patterns:

### Exec engine (send → detect completion → capture → clean)

Port their three-tier `executeStrategy` as our completion tiers:

| Tier | VS Code mechanism | Our equivalent |
|---|---|---|
| Rich | OSC 633 sequences (633;A prompt, B cmdline, C exec, D done+exit, E line) via `ICommandDetectionCapability` | **We inject 633 ourselves**: send command wrapped with emitted markers — ConPTY/conhost pass VT through; WT/pwsh already emit 633 when shell integration on. Detect `;D;` + exit code in buffer tail |
| Basic | `onCommandFinished` + idle-prompt wait | Same on partial marker output |
| None | `sendText` + idle detection (≈1s data-silence) + marker slicing | **Our default**: record buffer len/cursor as start-marker → `type` → poll UIA/CONOUT$ until N ms stable → slice buffer → strip |

### Output pipeline (port 1:1)

- `findCommandEcho` — wrap-tolerant echo strip (whitespace-insensitive, double-echo case)
- prompt-suffix trimming — last line matching detected prompt style (PS/bash/cmd/`>`)
- `MAX_OUTPUT_LENGTH = 16000`, tail-truncated; spill oversized to file (`largeOutputFileWriter` equivalent → temp file + return path)
- `truncateOutputKeepingTail`

### Completion confidence

- **Premature-idle fix**: wait for cursor movement past send point BEFORE starting idle detection (they hit this bug — pwsh swallows early `\r`)
- Idle ≠ done: require output-stable N ms AND new prompt line detected (state machine `Initial→Prompt→Executing→PromptAfterExecuting`)
- **Sentinel `echo EXIT:$?`** — VS Code avoids (untrusted text), but for our buffer-only channel it's the cheapest reliable finish+exit-code signal: `send` appends `; echo CU_EXIT:$?` variant per shell (cmd: `echo CU_EXIT:%ERRORLEVEL%`)
- Alt-buffer abort: detect vim/htop/fullscreen apps (buffer switches) → return "interactive app, detach"

### Input-needed detection (`outputMonitor` port)

- strict last-line regexes: y/n, password/passphrase, `(END)` pager → flag `input_needed`
- broad `: $`/`: ?` trailers gated on consecutive idle polls (they had false-positive history — keep strict set only, route password prompts to user)

### Safety gate (their `commandLineAutoApprover` port)

- sub-command split (`;` `&&` `|` pipes) — **deny wins**, never single-regex on raw line
- rule table `{"cmd|/regex/": true|false}` — defaults: allow read-only, deny rm/del/kill/format
- `ConfirmTerminalCommandTool` equivalent: `send --confirm` flag requiring explicit approval per command on bound (user-owned) terminals; spawn sessions default-allow
- disclaimers for `curl|wget|eval|iex` (prompt-injection surface)

### Typing

- bracketed-paste wrap for multiline: `ESC[200~ … ESC[201~` — avoids readline corruption on pwsh/bash

### Terminal selection

- dedicated session per task = our `spawn` mode; `GIT_PAGER=cat`, `TERM`/`PAGER` env hygiene
- `isBackground` executions → `get_terminal_output <id>` follow-up reads (our `send --bg` + `recv`)

## Open questions for implementation

1. WT multi-tab/pane: multiple `TermControl`s per window → bind to focused/active one (UIA HasKeyboardFocus) or `--tab-index`.
2. conhost `AttachConsole` on elevated shell from non-elevated agent → likely access denied; document degrade to pixel path.
3. `wsl.exe` pipe spawn: include `WSL_UTF8=1` env; optional tmux control mode later.
4. Resize: `ResizePseudoConsole` only for spawn mode (winpty has `PTY.set_size`).
