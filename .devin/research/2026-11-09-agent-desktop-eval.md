# Eval: agent-desktop (issue #423) - 2026-11-09

Source video: youtu.be/iEhCLn9utDU ("Agent Desktop", Prism Labs).
Correction: video said "Virsel Labs" - actual org is **vercel-labs**
(Next.js company = Vercel; whisper misheard).

## What it is

`vercel-labs/agent-desktop` - Apache-2.0, ~19.2k stars, v1.2.0 (2026-11-05).
Rust core (`agent-desktop-core`) + per-OS platform crates:
macOS AXUIElement, Windows UI Automation, Linux AT-SPI2. Ships as npm CLI
(`npm i -g agent-desktop`, Node>=18, native binaries x64/ARM64), C library,
and MCP server. **No model inside** - pure perceive/act tool; the
observe→act→verify loop lives in the caller. Every command prints one
JSON envelope (`ok`/`data`/`error`). Stable element refs (`@snap:eN`)
survive across snapshots; actions retry-safe.

Sibling project: `agent-desktop.dev` / xa11y - Playwright-style library
for native apps; agent-desktop is the CLI/MCP product on top.

## Live verification (this machine, Windows 11)

- `npx agent-desktop status` → `platform: windows`,
  `accessibility: granted` (UIA already permitted), supported surfaces:
  window, focused, sheet, menu, start-menu, taskbar, system-tray,
  system-tray-overflow, action-center.
- `list-apps` → Discord.exe, WindowsTerminal.exe (Arc/Chromium absent -
  needs `--cdp` DevTools path or doesn't expose UIA).
- `snapshot --app WindowsTerminal -i --compact` → full UIA tree JSON:
  roles, names, `native_id` (automation_id), `available_actions`, stable
  `ref_id`s, `snapshot_id`. Read our own terminal tab title correctly.
- Commands cover: snapshot/find/get/is, click/double/triple/right-click,
  type/set-value/clear/focus/select/toggle/check/uncheck/expand/collapse,
  scroll/scroll-to, press/key-*/hover/drag/mouse-*, launch/close-app,
  list-windows/list-displays/list-apps/focus-window, clipboard,
  screenshot (PNG fallback), notifications, windows.
- Physical input (double-click, hover, drag, mouse-*) gated behind
  `--headed`; semantic actions work headless. `skills get desktop` +
  `skills get platform` ship compiled per-version agent guides - same
  pattern as our SKILL.md but version-locked to binary.

## Fit with devin-bundle

- `extensions/computer-use` today: screenshot+perception pipeline
  (cu-perception/cu-realtime efforts archived but extension lives).
  agent-desktop is the missing fast perception layer: deterministic refs
  instead of pixel matching, ~50-200ms vs seconds per look.
- Integration seam options:
  a) CLI wrapper inside computer-use (call `agent-desktop snapshot/find/
     click`) - smallest change, reuses JSON envelope.
  b) MCP server - bundle already has MCP plumbing; zero-code tool surface.
  c) Rust core via our rust-core crates - heavier, only if we need in-proc.
- Gaps: canvas/game/custom-drawn UIs publish no AX tree (same limit as
  screen readers) → screenshot fallback still needed; Electron apps need
  `--cdp` route; unsigned binary blocked by Smart App Control on clean
  Win11 (checksum verify documented).

## Recommendation

**ADOPT-EVAL → bounded spike.** File follow-up: add agent-desktop as an
optional backend in computer-use (`CU_BACKEND=agent-desktop`), AX-first
with screenshot fallback, behind the existing confirm gates. Verify on
Windows UIA targets (Explorer, Settings, our own tools) before touching
the perception pipeline. Not a replacement for web automation
(agent-browser remains that layer).

## Evidence

- Repo: github.com/vercel-labs/agent-desktop (Apache-2.0)
- Docs: agent-browser.dev/desktop
- Local run: status/list-apps/snapshot outputs above (state_root
  `C:\Users\leand\.agent-desktop`, session state gitignored-by-design)
