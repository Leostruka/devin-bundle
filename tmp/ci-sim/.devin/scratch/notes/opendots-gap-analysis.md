# OpenDots x devin-bundle: bidirectional gap analysis

Date: 2026-10-06. Sources: github.com/CopilotKit/OpenDots @main (fetched today),
github.com/CopilotKit/OpenBot @b6932d3 (pinned by OpenDots), copilotkit.ai/opendots.
Bundle side: this repo, paths cited inline. OpenDots side: repo paths under
`CopilotKit/OpenDots` unless noted. Full OpenDots source notes: `.devin/research/opendots-map.md`.

## 1. What each thing is

| | devin-bundle | OpenDots |
|---|---|---|
| Kind | Harness layer for the Devin CLI agent: rules, 67 skills, hooks, subagent profiles, local-tool extensions | Self-hosted single-owner "AI coworker workspace" template: web app + agents (alpha, MIT) |
| Runtime | Devin CLI process (external); bundle configures it via install.ps1/install.sh into %APPDATA%\devin | Node 24 Hono server :4310 + React/Vite client :5173 + SQLite (docs/SETUP.md) |
| Agent loop | Devin CLI native loop, unbounded turns, tool calls = exec/read/write/etc. | `DotAgent` -> CopilotKit `BuiltInAgent` -> TanStack AI `chat()`, OpenAI-compatible chat-completions only; 90s turn cap, maxIterations 5/10, max_completion_tokens 2200 (src/server/dot-agent.ts) |
| Persistence | Filesystem + git (.devin/, ledgers, research/) | SQLite (pages/config/threads) + CopilotKit Intelligence (conversation history, MANDATORY for chat) |
| Distribution | install.ps1/install.sh file copier + venvs | git clone + npm ci + .env |
| Tests | 1588 collected (pytest tests/) | ~30 vitest files (tests/) |

## 2. Capability matrix

| Axis | devin-bundle | OpenDots | Edge |
|---|---|---|---|
| Screen perception | mss capture, --grid, UIA hint sidecars (TTL+generation+session bound), WinRT OCR->coords, WGC per-window/occluded frames + FrameArrived waits, pixel edge-detection probe (extensions/computer-use/USAGE.md: cu_hints, cu_ocr, cu_wgc, cu_probe, cu_events) | Browser-only: Playwright ARIA snapshot w/ ref+snapshotId binding, screenshot jpeg (OpenBot agent-computer/src/index.ts, aria-snapshot.ts) | **bundle** (OS-wide vs one browser DOM) |
| GUI action | Physical input w/ profiles (fast/smooth/human, bezier/minjerk, Fitts timing, seeded), UIA Invoke/SetValue, scoped channels PostMessageW/UIA/WriteConsoleInputW/CDP, ghost-cursor overlay (USAGE.md scoped-channel table) | Element-ref click/type/key/scroll inside container Chromium; human takeover via x/y on CDP screencast (src/shared/computer-types.ts) | **bundle** (no OS-level actuation in OpenDots) |
| Terminal | Bind WT/conhost/mintty (UIA TextPattern, CONOUT$, OCR) + own PTY spawn daemon, command gate, agent->agent `link` piping (extensions/computer-use/cu_terminal.py, terminal.py, terminal_sessions.py) | `computer_exec`: bounded command in container, 60s cap (computer-types.ts `exec`) | **bundle** |
| Browser | Attach-only bound browser: CDP (Chromium) / BiDi (Firefox, Zen); eval/console/errors/requests/wait/cookies/storage/find/tabs + events daemon HAR-lite (USAGE.md browser.py section). User must launch with --remote-debugging | Agent-owned Chromium per Dot, persistent profile/logins across restarts, human "Take over" live view (docs/COMPUTERS.md; OpenBot profiles.ts, screencast.ts, control.ts) | **OpenDots** on ergonomics (agent-owned persistent profile + takeover); bundle on protocol breadth (BiDi, host browser attach) |
| Isolation | QEMU VM via QMP: spec digest + TTY consent + image sha256 pin + closed profile (network off), virtio-serial guest worker (exec/dom/uia/clipboard), ADB attach-only devices, Linux container profile (env.py, cu_qmp*, cu_guest*, cu_adb_backend.py) | Docker container per Dot (shared host kernel), per-Dot HMAC-derived token, volumes for profile+workspace, optional gVisor runsc, NO default egress policy (docs/COMPUTERS.md; compose.computers.yml) | **bundle** (VM > container; egress explicit) |
| Governance | PreToolUse/PostToolUse/Stop/SessionStart/UserPromptSubmit/PostCompaction hooks: pre-exec-guard, pre-write-guard, destructive-gate, check-push-green, architecture-gate (manifest required), constraint-pinning, validate-skill-format, check-ai-signature (hooks.v1.json; scripts/*.py). system-control: DENY/CONFIRM/ALLOW + one-shot digest-bound confirmation tokens, JEA/polkit broker seam (extensions/system-control/USAGE.md) | Per-Dot booleans (browser/files/shell/research/memory/Space) checked app-side; 100ms watcher aborts run on permission change; global pause; HITL `review_space_page` card; audit 1000 actions/Dot EXCLUDING typed values/file contents (dot-agent.ts; runner.ts; docs/COMPUTERS.md). No hook system; computer itself has no policy engine | **bundle** for enforcement depth; **OpenDots** for per-agent permission matrix UX |
| Skills/extensibility | 67 file skills + routers (ask-bundle/leo), self-extend, writing-skills, devin-config; skills carry scripts/ (skills/; manifest.json) | Intelligence "Automatic Learning" only: >=15 threads analyzed, human publishes, `copilotkit_load_skill`/`copilotkit_read_skill_file` injected (docs/SETUP.md; src/server/tanstack-tools.ts). No user-authored skill files | **bundle** (authoring+delivery local); OpenDots adds auto-synthesis |
| Models | SWE-2 medium/high/max, effort-routed, env overrides; Devin CLI supplies models (data/bundle-models.json) | Any OpenAI-compatible endpoint for compute; OpenAI Realtime hardcoded for voice (.env.example; dot-agent.ts; voice.ts) | different axes: bundle = fixed catalog+effort routing; OpenDots = any OpenAI-compat endpoint |
| Multi-agent | 6 subagent profiles w/ per-role model pinning; devin-N.ps1 up to 4 parallel CLI instances + git worktrees + wt panes; terminal `link` agent->agent piping; afk-loop issue DAG (agents/*.md; devin-N.ps1; terminal.py link) | Multiple isolated Dots (own threads/computer/Space), NO Dot->Dot messaging, group chats = future work (site FAQ) | **bundle** (coordination exists) |
| HITL | Confirmation tokens (system-control), PermissionRequest hook, env TTY consent, destructive-gate | In-chat approve/decline cards (CopilotKit HITL), human takeover of live browser | OpenDots on UX; bundle on binding strength |
| Channels | CLI/TUI only; social-midia outbound posting; jira integration | Web chat, page-chat, Slack (managed Channels SDK, allowlists), voice calls (OpenAI Realtime + ask_compute delegation, 15min/6-turn caps), background scheduled turns | **OpenDots** |
| Background work | afk-loop skill (in-session DAG); heartbeat/cron pruned (primeagent-reference: no daemon to reattach) | SQLite claim/lease runner, 90s cap, "scheduled turns in original conversation" (runner.ts; site status table) | **OpenDots** |
| Memory/learning | .devin/memory MOC + memory-* hook pipeline; self-improvement refine loop + refinements.log.jsonl + held-out evidence rule (AGENTS.md rule 15) | Flat `Preferences:` list injected in prompt; Intelligence learned-skills pipeline | **bundle** on discipline; OpenDots on automation of skill proposal |
| Cost/deps | No SaaS required; stdlib hooks; extension venvs | Hard deps: Intelligence (hosted/licensed/30-day local eval), OpenAI-compat key, Docker for computers; Parallel MCP for search | **bundle** (self-contained) |

## 3. Gaps the bundle has vs OpenDots (adopt/ignore)

| # | Gap | Evidence (OpenDots) | Impact for local GUI automation | Effort | Verdict |
|---|---|---|---|---|---|
| B1 | Agent-owned persistent browser: bundle browser.py is attach-only ("Nothing is launched or auto-attached", USAGE.md); OpenDots gives each agent its own Chromium profile surviving restarts + human takeover | OpenBot agent-computer (profiles.ts, control.ts, screencast.ts); docs/COMPUTERS.md | HIGH: agents keep logins without borrowing user's browser; removes --remote-debugging setup friction | LOW-MED: launchPersistentContext on existing playwright-less stack or bound-browser "managed profile" mode | **ADOPT** (light version: `browser.py launch --profile <name>` owning a Chromium user-data-dir under .devin/, reuse existing CDP path) |
| B2 | Persistent audit log per action: OpenDots records every computer action {actor, action, outcome} | docs/COMPUTERS.md "Activity" (1000 records, excludes payloads) | MED: forensics + refine-loop evidence; bundle contracts report status but don't persist a trail | LOW: append JSONL in cu_actions result path | **ADOPT** |
| B3 | Scheduled/background turns: OpenDots Runner claims SQLite tasks every 1s, 90s cap, resume on restart | src/server/runner.ts; site "Background work: scheduled turns" | MED: "always-on" automation; bundle pruned heartbeat (no session re-entry) but OS Task Scheduler + `devin -p` one-shot is viable | MED | **CONSIDER**: minimal scheduler recipe skill (Task Scheduler -> headless turn -> ledger), not a daemon |
| B4 | Per-agent permission matrix (browser/files/shell booleans per identity, runtime re-check aborts run) | dot-agent.ts `check()` watcher; computer-types.ts permissions schema | LOW-MED: bundle has global hooks + capability tokens, not per-subagent permission scopes | MED | **CONSIDER**: subagent profiles already pin tools; a permissions field per profile is cheap sugar |
| B5 | In-chat HITL cards (approve/decline pausing a tool call) | src/shared/page-review.ts; PageReviewCard.tsx | LOW: confirmation tokens + PermissionRequest cover semantics | HIGH (needs UI) | **IGNORE** (UI-bound) |
| B6 | Spaces/pages document workspace (tiptap editor, autosave, revision checks) | src/server/pages.ts; src/client/editor/ | LOW for automation; artifacts already land as files/git | HIGH | **IGNORE** |
| B7 | Voice channel | src/server/voice.ts (OpenAI Realtime only) | LOW | HIGH | **IGNORE** |
| B8 | Slack/managed channels | slack-channel.ts; docs/SETUP.md#slack | LOW-MED (remote trigger) | MED | **IGNORE** now; file-drop queue suffices locally |
| B9 | AG-UI protocol + inline tool renderers (live computer view in chat) | README architecture; ComputerPanel.tsx | N/A for CLI | HIGH | **IGNORE** for bundle; note as interop option if a UI is ever built |
| B10 | Auto-synthesized skills from thread evidence (Automatic Learning pipeline) | docs/SETUP.md "Automatic Learning" | LOW-MED: bundle refine loop is stronger on evidence, weaker on auto-proposal | MED | **PARTIAL**: borrow "proposal queue + human publish" shape for self-improvement output; keep local |
| B11 | Live view of the agent browser: CDP screencast pushes JPEG frames on page change (everyNthFrame:1, q70, <=1280x800) with per-frame ACK backpressure, over WebSocket | OpenBot agent-computer/src/screencast.ts | MED: event-driven browser reperception instead of screenshot polling; user can watch bound-browser work live | LOW-MED: cu_browser.py already speaks raw CDP (Input.dispatch*, _WSClient.call); missing piece is Page.startScreencast + frame sink | **CONSIDER**: `browser.py watch` writing frames to temp for agent `read`; optional human viewer later |
| B12 | Takeover/handback state machine: one watcher at a time (ViewerSlot claim/supersede), human input forwarded via Input.dispatch* into the page, `resumeSnapshotRequired` forces fresh snapshot after handback | OpenBot agent-computer/src/{viewer,screencast}.ts; src/shared/computer-types.ts ComputerControl | LOW-MED: user is at the machine for host work; matters for remote/headless browsing only | MED | **CONSIDER**: bundle hint-generation invalidation already covers the stale-snapshot half; port only if remote viewing lands |

Note on "overlay": OpenDots has NO on-screen overlay - its visual surface is remote
view + takeover only. The bundle's cu_overlay.py (ghost cursor, UIA-bounds
annotations, WDA_EXCLUDEFROMCAPTURE) is the capability OpenBots lacks, not the
reverse. B11/B12 are the only portable pieces in that space.

## 4. Gaps OpenDots has vs the bundle (what it cannot do)

| # | Missing in OpenDots | Evidence | Bundle cover |
|---|---|---|---|
| O1 | Any OS-level GUI automation: no UIA, no pixel input, no OCR, no capture outside its browser | computer-types.ts (navigate/click/type on refs only); index.ts "Elements are addressed by reference, not by pixel" | extensions/computer-use entire stack |
| O2 | Anything Windows-native: computers are Linux containers; the app runs on Node (cross-platform) but automation = Linux Chromium | agent-computer/Dockerfile (ubuntu:24.04); docs/COMPUTERS.md | UIA/WinRT/WGC/WriteConsoleInputW/conhost paths |
| O3 | Terminal/PTY control | none (exec in container only) | terminal.py, terminal_sessions.py, system-control sessions |
| O4 | VM-grade isolation / closed network profile / image pinning | Docker shared kernel; runsc optional; "does not configure a restrictive network-egress policy" (docs/COMPUTERS.md) | QEMU/QMP envs, sha256 image verify, virtio-serial guest worker, ADB |
| O5 | Lifecycle hooks / pre-action gates on agent behavior; no destructive-action gate, no push-green gate, no manifest gate | none in repo; enforcement = permission booleans + prompt text | hooks.v1.json + scripts/*.py (11 hook points wired) |
| O6 | Non-OpenAI models; no model routing/effort levels | openaiCompatibleText chat-completions only (dot-agent.ts) | swe-2 tier routing (data/bundle-models.json); Devin CLI model layer |
| O7 | Agent-to-agent coordination; multi-Dot collab listed as future work | site FAQ | devin-N.ps1 multi-instance, terminal link, subagent profiles, afk-loop |
| O8 | Local skill authoring/shipping; user skills are not in the template | learning is Intelligence-server-side only | 67 skills + writing-skills + self-extend |
| O9 | Test/evidence gates around agent output (audit records outcome but nothing gates on it) | runner.ts finish/fail only | gates ledgers, check-push-green, held-out rule, audit.py |
| O10 | Works without external SaaS: requires Intelligence + model key for ANY chat | dot-agent.ts config check throws without intelligenceKey/apiKey/model | fully local (minus model API) |
| O11 | Policy/audit gateway: full OpenBot has one ("one gateway that decides and records it", OpenBot README); OpenDots template dropped it - computer's only auth is the token | agent-computer index.ts: "no policy engine... its direct-port boundary is the computer token" | system-control DENY/CONFIRM/ALLOW + token digests |

## 5. Verdict

**For local Windows GUI automation, OpenDots covers nothing the bundle needs.** Its
"computer" is a per-agent Linux container running one Chromium with ARIA-ref
actions, persistent logins, files, and a bounded shell (OpenBot agent-computer,
pinned b6932d3). That is a well-built browser-workspace primitive with good
defaults (per-Dot derived tokens, permissions off by default, takeover, honest
status table), but it operates on zero of the surfaces the bundle's computer-use
targets: no UIA, no OCR, no pixel/coordinate input for the agent, no terminal
control, no host process/service control, no VM isolation. The two systems solve
adjacent but non-overlapping problems: OpenDots = persistent multi-agent web
workspace; bundle = governed local agent with real desktop reach.

**Worth porting (in priority order):**

1. **Agent-owned persistent browser profile + takeover pattern** (B1). Highest
   real impact: today the bundle borrows the user's browser via CDP attach;
   owning a dedicated Chromium user-data-dir per task keeps cookies/logins
   agent-side and removes the manual `--remote-debugging` step. Port the
   *pattern*, not the stack: no supervisor, no container, just launch+persistent
   context feeding the existing `browser.py` CDP path.
2. **Append-only action audit JSONL** (B2). Cheap, feeds forensics and the
   refine loop's evidence rule (AGENTS.md rule 15).
3. **Scheduled-turn recipe** (B3): OS Task Scheduler -> `devin -p` headless ->
   ledger, documented as a skill. Validates the always-on shape without a daemon.

**Explicitly not worth it:** Spaces UI, voice, Slack, AG-UI renderers, managed
learning pipeline, and the Intelligence dependency itself. Each is UI- or
SaaS-bound, none improves local GUI automation, and Intelligence is a hard
external dependency the bundle deliberately avoids.

**Caution adopted as design input, not code:** OpenBots's full gateway (policy
+ audit before every action) exists in OpenBot but was dropped from OpenDots;
the bundle's system-control CONFIRM tokens + hook layer already match that
gate's semantics locally. OpenDots' honest-status table (tested-with-live vs
tested-locally vs needs-live-testing) is a cheap documentation pattern worth
copying into USAGE.md headers.

## 6. Verification notes

- Bundle claims verified by reading: hooks.v1.json, config.json,
  extensions/computer-use/USAGE.md (full), extensions/system-control/USAGE.md,
  extensions/scrape-tools/USAGE.md, data/bundle-models.json,
  data/bundle-integrations.json, install.ps1 header, audit.py header,
  agents/researcher.md, devin-N.ps1 header; `pytest --collect-only` = 1588
  tests; skills/ = 67 dirs.
- `.devin/research/bundle-capability-map.md` (2026-09-26) claims "no directed-
  input mechanism exists" - STALE: scoped channels (PostMessageW/UIA/
  WriteConsoleInputW/CDP) now exist per USAGE.md lines 582-645. Direct reads
  supersede the map (Rule 12).
- OpenDots claims verified by reading repo files at main today: dot-agent.ts,
  computer-tools.ts, computer-types.ts, page-tools.ts, runner.ts, voice.ts,
  parallel.ts, headless.ts, learning.ts, tanstack-tools.ts, browser/index.ts,
  package.json, .env.example, compose.computers.yml, deployment/computers/*,
  docs/{SETUP,COMPUTERS}.md; OpenBot agent-computer/{Dockerfile,src/index.ts,
  src/screencast.ts,src/viewer.ts,src/live-page.ts} at pinned rev;
  copilotkit.ai/opendots.

## 7. Adoption status (post-implementation, 2026-10-06)

Implemented on branch `feat/opendots-adaptations` per
`.devin/plans/2026-10-06-opendots-adaptations.md`:

| Gap | Status | Commit(s) |
|-----|--------|-----------|
| B1 agent-owned browser | ADOPTED | 5d8d842, a126ed8 (`browser.py launch/stop`) |
| B2 action audit JSONL | ADOPTED | 78797d8, 0a57686, 05f79f2 (`cu_audit.py` + `result()` hook; cmd leak fixed: argv[1] never audited) |
| B3 scheduled turns | ADOPTED | d176554 (`skills/scheduled-turns`; recipe corrected to `--prompt-file` in 05f79f2) |
| B10 proposal queue | ADOPTED | 29aeff5 (`self-improvement` publish gate) |
| B11 screencast watch | ADOPTED | fe63cae (`browser.py watch`, CDP-only) |
| B4 per-agent permissions | DROPPED | `agents/*.md` `allowed-tools:` already scopes tools; ephemeral subagents have no mid-run revocation surface |
| B12 takeover/handback | DEFERRED | revisit only if remote viewing lands |

Final whole-branch review clean; 1604 tests + audit.py green.
