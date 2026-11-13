# OpenDots architecture map (primary sources only)

Repo: github.com/CopilotKit/OpenDots (MIT, alpha, TypeScript, ~43 commits at fetch time, 3.8k stars).
All file paths below are in that repo unless noted. Fetched 2026-10-06.

## What it is

- Self-hosted, single-owner "AI coworker workspace" template. Not a hosted product. (README.md; copilotkit.ai/opendots)
- Node 24 + npm. React 19/Vite client on :5173, Hono API server on :4310, SQLite at DATABASE_PATH for pages/Dot config/thread bindings/work metadata. (docs/SETUP.md; package.json; src/server/index.ts)
- Conversations persist in CopilotKit Intelligence (hosted service, licensed self-host, or local Docker eval on macOS). Thread history is NOT in SQLite. (README.md; docs/SETUP.md)

## Agent runtime

- `src/server/dot-agent.ts`: `DotAgent extends AbstractAgent` (@ag-ui/client) wrapping CopilotKit `BuiltInAgent` (@copilotkit/runtime/v2), factory returns TanStack AI `chat()` with `openaiCompatibleText` adapter, `api: 'chat-completions'`. Any OpenAI-compatible endpoint via OPENAI_BASE_URL/OPENAI_MODEL/OPENAI_API_KEY.
- Hard bounds: `TURN_TIME_LIMIT_MS = 90_000` (dot-agent.ts); `agentLoopStrategy: maxIterations(5)` or 10 when skill delivery on; `max_completion_tokens: 2200`.
- System prompt is a template literal: role name + instructions + tool-usage rules + "memories" (flat text list from SQLite, injected as `Preferences:`) + current page context (marked untrusted) + UTC time. (dot-agent.ts)
- Client-sent system/developer messages are stripped before conversion (trust boundary). (dot-agent.ts, `convertInputToTanStackAI` call)
- Same DotAgent serves web chat, Slack threads, scheduled turns, and voice compute delegation. (README.md; src/server/headless.ts; src/server/voice.ts; src/server/slack-channel.ts)
- Headless turns: `runThreadTurn()` opens an `IntelligenceAgent` WS connection to the runtime and runs one turn (used by voice compute + scheduled work). (src/server/headless.ts)
- Background work: `Runner` polls SQLite `store.claim()` each second, one active run, lease+ownership checks every 100ms, 90s abort, finish/fail recorded. (src/server/runner.ts)

## Tool inventory (agent-facing)

| Group | Tools | Source |
|---|---|---|
| Pages | `list_authorized_spaces`, `list_space_pages`, `read_space_page`, `create_space_page`, `edit_space_page` (revision-checked, Space-scoped) | src/server/page-tools.ts |
| HITL | `review_space_page` (client-side tool; CopilotKit card pauses for Approve & save / Decline) | src/shared/page-review.ts; dot-agent.ts (input.tools filter) |
| Web research | `search_web`, `read_public_page` via Parallel MCP endpoint `https://search.parallel.ai/mcp` (web_search + web_fetch tools, MCP StreamableHTTP client, 60s bound, 5 source cap, URL validation) OR read-only browser service | src/server/parallel.ts; dot-agent.ts |
| Read-only browser | `POST /browse`: Playwright chromium headless, JS disabled, GET-only, resource-type allowlist (document/stylesheet/image/font), 50 req cap, redirect re-validation, text 30k + jpeg screenshot. Separate process (`npm run browser`). | src/browser/index.ts, security.ts, transport.ts |
| Computer | `computer_navigate`, `computer_read`, `computer_snapshot`, `computer_screenshot`, `computer_click`, `computer_type`, `computer_key`, `computer_scroll`, `computer_files_list`, `computer_files_read`, `computer_files_write`, `computer_exec` | src/shared/computer-types.ts; src/server/computer-tools.ts |
| Human takeover | `human_click(x,y)`, `human_type`, `human_key`, `human_scroll` - owner-only, excluded from agent tools | src/shared/computer-types.ts; computer-tools.ts (filters `human_*`) |
| Learned skills | `copilotkit_load_skill`, `copilotkit_read_skill_file` (from Intelligence learned-skills container catalog) | src/server/tanstack-tools.ts; docs/SETUP.md "Automatic Learning" |

## Dot computers (OpenBot-derived)

- Built from pinned OpenBot revision `b6932d31...` via BuildKit git context; no moving tag. (compose.computers.yml; deployment/computers/README.md)
- `agent-computer/Dockerfile` (OpenBot repo): ubuntu:24.04 + Bun + Playwright 1.62.1 chromium, WORKSPACE_DIR=/workspace volume, PROFILES_DIR=/profiles volume, service on :4100.
- `agent-computer/src/index.ts` (OpenBot): ONE long-lived Chromium per container; elements addressed by ARIA ref via Playwright `aria-ref` engine, NOT pixels; `snapshotId` binds click/type to a fresh snapshot; persistent browser profile keeps logins across restarts; HTTP API guarded by COMPUTER_TOKEN; no policy engine inside computer (caller enforces); optional Xvfb virtual display for headed mode; CDP screencast for live view; modules for egress, secret-masking, control state machine, workspace confinement.
- OpenDots patch: each computer gets `HMAC-SHA256(COMPUTER_TOKEN, "opendots-computer:"+dotId)` instead of master token; supervisor keeps ensure/stop/reset/list + ownership checks; fail-closed build if upstream changes. (deployment/computers/README.md; deployment/computers/harden-supervisor.mjs)
- Per-Dot permissions `{enabled, browser, files, shell}` start disabled, enforced app-side in computer-service.ts; revoking cancels active request. Activity audit keeps 1000 records/Dot, deliberately EXCLUDES typed values, file contents, full commands. (docs/COMPUTERS.md; src/shared/computer-types.ts)
- Isolation: standard Docker containers, shared host kernel, no default restrictive egress policy; optional `COMPUTER_RUNTIME=runsc` (gVisor) if already installed; 2GB memory default; only supervisor mounts docker.sock; supervisor cap_drop ALL + no-new-privileges. (docs/COMPUTERS.md; compose.computers.yml)
- Takeover: human clicks/types in browser via CDP screencast; agent must take fresh snapshot after handback. (docs/COMPUTERS.md; agent-computer/src/control.ts, screencast.ts)

## Governance / permissions

- Per-Dot: role instructions, Space access list, `researchAllowed`, `memoryAllowed`, `skillDeliveryEnabled`, learningContainerId, computer permission booleans. (src/server/workspace.ts; dot-agent.ts `check()`)
- Runtime enforcement: 100ms watcher aborts the run if settings/permissions changed mid-turn; global `paused` killswitch. (dot-agent.ts; runner.ts ownership check)
- Workspace file paths confined to relative paths, traversal rejected. (computer-types.ts `path` schema; OpenBot agent-computer/src/workspace.ts)
- URL policy: http/https only, no userinfo creds, no redirects (browser tool), SSRF guards in navigation.ts + browser/security.ts.
- Secrets: server-side only; per-Dot derived computer token; BROWSER_SECRET >=24 chars timing-safe compare. (deployment/computers/README.md; src/browser/index.ts)
- No hooks/lint/test gates on agent output; no equivalent of PreToolUse/PostToolUse user hooks. Agent-side guardrails are prompt instructions + tool schema validation + permission booleans.

## Multi-agent model

- Multiple specialist Dots: name, role, instructions, own threads, own computer, own Space access. Isolation between Dots verified by tests ("second cannot list first's files"). (docs/COMPUTERS.md)
- No Dot-to-Dot messaging; site lists "multi-Dot group conversations" as further work. Single-owner identity model (Slack users map to owner). (copilotkit.ai/opendots FAQ; docs/SETUP.md)
- Parallel work = separate conversations per Dot, not coordinated agents.

## Channels & IO

- Web chat (CopilotKit React SDK), page-scoped chat threads. (README.md; src/client/)
- Slack: managed channel via `@copilotkit/channels` (Channels SDK) + Intelligence adapter; allowlist SLACK_TEAM_ID + SLACK_USER_IDS; threads bind to Dot. (docs/SETUP.md; src/server/slack-channel.ts)
- Voice: OpenAI Realtime API HARDCODED (`https://api.openai.com/v1/realtime/calls`, WebRTC SDP), semantic_vad, gpt-4o-mini-transcribe input, `ask_compute` function tool delegates long work to same Dot thread (90s, 6 compute-turn cap/call, 15min call cap); transcript receipt summarized into thread. (src/server/voice.ts)
- Background work: "scheduled turns in their original conversation" via Runner + SQLite tasks; pause/retry supported. (copilotkit.ai/opendots status table; runner.ts)

## Models

- Compute: any OpenAI-compatible chat-completions endpoint (OPENAI_BASE_URL). Demos used gpt-5.4-mini. (dot-agent.ts; docs/demos/README.md)
- Voice: OpenAI Realtime only. (voice.ts)
- No Anthropic/Gemini/local-adapter code paths in repo.

## Learning / memory

- Automatic Learning: Intelligence-side. Container per workflow; >=15 eligible threads default threshold; human reviews + publishes proposed skills in Intelligence dashboard; OpenDots per-conversation enrollment; delivery injects skill catalog into systemPrompts + load/read tools; denial fails the turn. (docs/SETUP.md "Automatic Learning"; dot-agent.ts learnedSkills config; tests/fixtures/learning-skills.zip)
- Memory: flat memory list in SQLite injected as `Preferences:` JSON in system prompt; `memoryAllowed` global+per-Dot. (dot-agent.ts; src/server/store.ts)

## Tested-status table (from site, honest alpha labeling)

- Tested with live services: conversations, spaces/pages, dot computers, calls.
- Tested locally: specialist dots, background work.
- Needs live testing: spoken delegation, Slack.
- Further work: shared editing, invitations, file uploads, multi-Dot group conversations. (copilotkit.ai/opendots "Status" section)

## What OpenDots is NOT

- Not local desktop automation: computer = containerized Chromium + files + bounded shell on Linux. No OS-level GUI control, no native apps, no Windows UIA, no OCR, no pixel-coordinate agent actions (human takeover uses x/y only).
- Not a coding agent: no repo editing tools, no git tools, no test infra.
- Not multi-user / not an orchestrator: single owner, no agent-to-agent delegation except voice->compute (same agent).
- Not self-contained: hard dependency on CopilotKit Intelligence for ANY conversation (setup state otherwise); model key required; Docker required for computers.
