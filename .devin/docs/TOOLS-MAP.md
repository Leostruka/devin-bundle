# Tools Map - complete runtime mapping

Maps ALL tools, subagents, hooks, and configs of the Devin CLI runtime vs
what the bundle covers. Source: docs.devin.ai + observed runtime (validated
version: `{{VALIDATED_CLI_VERSION}}` in `data/bundle-identity.json`).

## Runtime tools (26 active + 2 mode-dependent)

| Tool | Category | Validator check | Description |
|---|---|---|---|
| `read` | File | abs path | Reads a file (absolute path) |
| `write` | File | abs path + parent dir | Writes/creates a file |
| `edit` | File | abs path + old≠new | Exact string edit |
| `apply_patch` | File | - (args vary) | Applies a patch (mode-dependent) |
| `notebook_read` | File | abs path | Reads a Jupyter notebook |
| `notebook_edit` | File | abs path | Edits a Jupyter cell |
| `grep` | Search | valid regex | Ripgrep search |
| `glob` | Search | pattern | Glob pattern matching |
| `find_file_by_name` | Search | pattern | File-name search |
| `exec` | Shell | non-empty + no null byte | Runs a shell command |
| `get_output` | Shell | - (trivial: shell_id) | Reads background shell output |
| `write_to_process` | Shell | - (trivial: shell_id) | Writes to an interactive process |
| `kill_shell` | Shell | - (trivial: shell_id) | Kills a background shell |
| `web_search` | Web | non-empty query | Web search |
| `webfetch` | Web | http(s) URL | Fetches a URL |
| `run_subagent` | Subagents | task + valid profile + max_parallel ≤ 3 | Spawns a subagent |
| `read_subagent` | Subagents | - (trivial: agent_id) | Reads subagent output |
| `skill` | Skills | invoke/list/search | Invokes/discovers a skill |
| `todo_write` | Planning | todos + valid status | Manages the todo list |
| `ask_user_question` | UI | questions + options | Asks the user |
| `browser_preview` | Browser | url + name | Opens a browser preview |
| `close_browser_preview` | Browser | - (trivial: preview_id) | Closes the preview |
| `request_scope` | Permissions | scope + path | Requests directory access |
| `mcp_call_tool` | MCP | server + tool | Calls an MCP tool |
| `mcp_list_tools` | MCP | - (no required args) | Lists MCP tools |
| `mcp_list_servers` | MCP | - (no required args) | Lists MCP servers |
| `mcp_read_resource` | MCP | server + uri | Reads an MCP resource |
| `exit_plan_mode` | Planning | - (no required args) | Exits Plan mode (mode-dependent) |

**Validator column = checks implemented in `scripts/validate-tool-args.py`
(19 entries in `CHECKS`). Available, mostly not wired:** `hooks.v1.json`
only routes `exec`, `write`, `edit`, and `notebook_edit` through the
consolidated guards that call the validator, so the checks for the other 15
tools (including `run_subagent`) exist in the script but never execute -
no matcher fires for them. Excluded tools (`get_output`, `write_to_process`,
`kill_shell`, `read_subagent`, `close_browser_preview`, `mcp_list_tools`,
`mcp_list_servers`, `apply_patch`, `exit_plan_mode`) fail clearly without
validation.

## Subagents (8 profiles)

| Profile | Type | Model | Tools | Bundle agent file |
|---|---|---|---|---|
| `subagent_explore` | Built-in | Default router (see `data/bundle-models.json` aliases) | Read-only + web_search | - (built-in) |
| `subagent_general` | Built-in | Inherits parent (`{{BUNDLE_DEFAULT_MODEL}}`) | Full (fg) / pre-approved (bg) | - (built-in) |
| `architect` | Custom | Max (`{{BUNDLE_MAX_MODEL}}`) | read, grep, glob, web_search, webfetch, mcp_* | `agents/architect.md` |
| `debugger` | Custom | Medium (`{{BUNDLE_MEDIUM_MODEL}}`) | read, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write | `agents/debugger.md` |
| `implementer` | Custom | Medium (`{{BUNDLE_MEDIUM_MODEL}}`) | read, write, edit, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write, notebook_*, mcp_* | `agents/implementer.md` |
| `qa-ci` | Custom | Medium (`{{BUNDLE_MEDIUM_MODEL}}`) | read, grep, glob, find_file_by_name, exec, get_output | `agents/qa-ci.md` |
| `researcher` | Custom | Max (`{{BUNDLE_MAX_MODEL}}`) | read, grep, glob, web_search, webfetch, mcp_* | `agents/researcher.md` |
| `reviewer` | Custom | Max (`{{BUNDLE_MAX_MODEL}}`) | read, grep, glob, exec, get_output | `agents/reviewer.md` |

Project-local profiles live under `.devin/agents/` (4 profiles, including
`repo-reviewer`; see `.devin/agents/README.md`).

**Model strategy:**
- `subagent_explore` (built-in): CLI default router - check
  `data/bundle-models.json` aliases; never dispatch in free-tier mode
  (AGENTS.md Rule 20).
- Custom agents: pin `{{BUNDLE_MAX_MODEL}}` (Max) or
  `{{BUNDLE_MEDIUM_MODEL}}` (Medium), per `data/bundle-models.json` and the
  `BUNDLE_MAX_MODEL` / `BUNDLE_MEDIUM_MODEL` env vars. Do NOT use unverified
  paid aliases (see `data/bundle-models.json`).
  - Without a pin, custom agents use the CLI default router (possibly paid).
- For work that needs the parent: use `subagent_general` (inherits parent)
  or pin `model: {{BUNDLE_DEFAULT_MODEL}}` in the agent file.

**VALID_PROFILES in validate-tool-args.py (12 names):**
architect, debugger, domain, implementer, issue-tracker, qa-ci,
repo-reviewer, researcher, reviewer, subagent_explore, subagent_general,
triage-labels. Note: the check is implemented but not wired - no hook
matcher routes `run_subagent` (see the tools table note above).

## Hooks (8 events, consolidated guards)

`hooks.v1.json` declares one entry point per matcher; each entry point is a
consolidated guard script that runs several gates in-process via
`_hookrun.py` (one Python spawn instead of N).

| Event | Matcher | Entry point | Gates run in-process |
|---|---|---|---|
| PreToolUse | `^exec$` | pre-exec-guard.py | destructive-gate, architecture-gate, check-ai-signature, check-push-green, validate-tool-args, no-em-dash |
| PreToolUse | `^(write\|edit\|notebook_edit)$` | pre-write-guard.py | always: architecture-gate, validate-tool-args, no-em-dash; write\|edit only: check-ai-signature, validate-mermaid |
| PostToolUse | `^(exec\|mcp_call_tool)$` | post-exec.py | silent-error-review, context-pressure, memory-post-exec, gh-pr-assignee |
| PostToolUse | `^(write\|edit)$` | memory-post-edit.py | memory-post-edit (memory injection by cues.path) |
| PostCompaction | - | constraint-pinning.py | constraint-pinning (detects dropped constraints; writes re-injection marker) |
| UserPromptSubmit | - | user-prompt.py | constraint-pinning, behavioral-nudge, memory-retrieval |
| SessionStart | - | session-start.py | constraint-pinning, context-budget |
| SessionEnd | - | memory-stop.py | memory-stop (logs `.devin/memory/` state) |
| Stop | - | stop-guard.py | check-ai-signature, refine-review-prompt, memory-stop, no-em-dash |

**Event available in the runtime but unused by the bundle:**
- `PermissionRequest` - fires when the agent needs a permission decision.
  Declared in `hooks.v1.json` with an empty hook list.

**Manual scripts (not hooks):**
- validate-refinement-evidence.py - verifies refinements.log.jsonl
- validate-skill-format.py - validates skill format
- validate-tool-args.py - argument checks for 19 tools; runs only inside
  the pre-exec/pre-write guards, so only `exec`, `write`, `edit`, and
  `notebook_edit` payloads ever reach it.

## Runtime configs

| Config | Location (bundle) | Location (Devin home) | Function |
|---|---|---|---|
| AGENTS.md | `./AGENTS.md` | `~/.config/devin/AGENTS.md` | Global rules (28 index entries: 20 rule bodies + 8 merged aliases; numbering gaps retained for stability) |
| config.json | `./config.json` | `~/.config/devin/config.json` | Model, hooks, theme |
| mcp_config.json | `./mcp_config.json` | `~/.config/devin/mcp_config.json` | MCP servers |
| hooks.v1.json | `./hooks.v1.json` | - (rendered into `config.json.hooks` at install) | Single hook source; also `.devin/` template |
| credentials.toml | `./credentials.toml` | - | Credentials (MASKED) |
| agents/ | `./agents/` | `~/.config/devin/agents/` | 6 user-level profiles |
| .devin/agents/ | `./.devin/agents/` | - | 4 project-local profiles (see `.devin/agents/README.md`) |
| skills/ | `./skills/` | `~/.config/devin/skills/` | 69 skills (`afk-loop` is a mode of `execution`, not a separate skill) |
| extensions/ | `./extensions/` | `~/.config/devin/extensions/` | Local utilities (e.g. `computer-use` - GUI automation; `system-control` - authorized OS control) |
| scripts/ | `./scripts/` | `~/.config/devin/scripts/` | 29 scripts (Python hooks + JS helpers) |
| docs/ (dissolved) | `./.devin/{docs,plans,templates}/` | `~/.config/devin/docs/` | Bundle documentation |
| MODEL-GUIDE.md | `./.devin/docs/MODEL-GUIDE.md` | `~/.config/devin/docs/MODEL-GUIDE.md` | Model guide (see `data/bundle-models.json`) |
| SKILL-TIERS.md | `./.devin/docs/SKILL-TIERS.md` | `~/.config/devin/docs/SKILL-TIERS.md` | Discovery by domain + costs |
| TOOLS-MAP.md | `./.devin/docs/TOOLS-MAP.md` | `~/.config/devin/docs/TOOLS-MAP.md` | This file |
| manifest.json | `./manifest.json` | - | Export manifest |
| .mcp.json | - (deny rule) | `~/.config/devin/.mcp.json` | Alternative MCP config |

**Runtime configs NOT in the bundle (not bundleable):**
- System prompt (Devin CLI runtime, injected by the CLI)
- Sandbox config (runtime, not persistent)
- Model picker state (runtime UI)
- Editor integration state (Windsurf, VS Code - runtime)
- Session state (conversation, not config)

## MCP Servers

The bundle loads MCP servers from `mcp_config.json` in the user's Devin
home. `mcp_config.json.example` contains an example issue-tracker
integration; integration parameters (site, cloud ID, enablement) live in
`data/bundle-integrations.json`. Authenticate before enabling; credentials
and local integration notes belong in local troubleshooting, not in the
global bundle.

**MCP audit (arXiv:2606.30317):**
- Tool count per server < 10-15 for >90% accuracy (Claude Haiku)
- 20-30 tools for Sonnet 4
- Check tool count with `mcp_list_tools` once the MCP server is logged in
- If >15 tools, consider the `mcp-governance` skill

## Devin CLI modes

| Mode | Command | Behavior |
|---|---|---|
| Normal | `/normal` | Asks approval for tools with side effects |
| Accept Edits | `/accept-edits` | Auto-approves workspace edits |
| Smart | `/smart` | Auto-approves actions a fast model judges safe |
| Plan | `/plan` | Read-only planning (no changes) |
| Bypass | `/bypass` | Auto-approves everything |
| Autonomous | - | Sandbox sessions only |

**Note:** the mode is controlled by the user in the UI, not by the agent.
In `normal` (default), the runtime asks approval for side-effect tools -
the runtime asks, not the agent.

## CLI commands (3000.11.x)

| Command | Type | Function |
|---|---|---|
| `devin --cloud` / `/cloud` | Cloud | Runs a Devin Cloud session from the CLI |
| `/handoff`, `/pickup` | Cloud | Brings a PR branch from a cloud session into a local session |
| `devin ssh` / `/ssh` | Cloud | Connects to a Devin Cloud VM |
| `devin forward` | Cloud | Port-forward from a cloud box to localhost |
| `devin rules`, `devin skills`, `devin plugins`, `devin doctor` | Config | Native rules/skills/plugins management and diagnostics |

**Note 3000.11.1:** an `otel` block in `config.json` or the
`OTEL_EXPORTER_OTLP_*` env vars export events/metrics to an OpenTelemetry
collector - not adopted (no collector configured; `devin doctor` already
validates the environment).

## Available models (Devin CLI `{{VALIDATED_CLI_VERSION}}`)

| model_uid | Label | Effort | Context | Cost | Recommended |
|---|---|---|---|---|---|
| `{{BUNDLE_DEFAULT_MODEL}}` | SWE-2 High (parent) | high | 262K | **Free** | ✓ (config.json) |
| `{{BUNDLE_MEDIUM_MODEL}}` | SWE-2 Medium | medium | 262K | **Free** | Simple tasks, spot fixes, isolated scripts |
| `{{BUNDLE_MAX_MODEL}}` | SWE-2 Max | max | 262K | **Free** | Open-ended tasks, global refactors, long-horizon |
| `paid_model_alias` | Paid alias | - | see registry | see registry | NEVER use without confirming `data/bundle-models.json` |
| `adaptive` | Paid router | see registry | - | see registry | Do not use in free mode |
| `opus` | Paid model | Anthropic | - | see registry | Do not use in free mode |
| `sonnet` | Paid model | Anthropic | - | see registry | Do not use in free mode |
| `gpt` | Paid model | OpenAI | - | see registry | Do not use in free mode |
| `codex` | Paid model | OpenAI | - | see registry | Do not use in free mode |
| `gemini` | Paid model | Google | - | see registry | Do not use in free mode |

**⚠️ CONDITIONAL policy:** when the parent runs a FREE model (read from
`data/bundle-models.json` with `cost_tier: free`), NEVER use paid models
for subagents. Short names/aliases (`opus`, `sonnet`, `codex`, `gemini`,
etc.) may resolve to paid entries - check `data/bundle-models.json` first.
Use the parent (`{{BUNDLE_DEFAULT_MODEL}}`) and the subagent models
(`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`) from the registry.
When the parent is paid, subagents may use paid models.

## Context budget (parent model)

Measured by bytes/4 (262K context window):

```
System prompt + tool defs    ~???? tok (Devin runtime, not measurable)
AGENTS.md                    ~2883 tok (1.10%)
SKILL-TIERS.md (if read)     ~3610 tok (1.38%)
MODEL-GUIDE.md (if read)     ~3820 tok (1.46%)
TOOLS-MAP.md (if read)       ~3432 tok (1.31%)
Invoked skills (1-3)         ~1000-9700 tok (0.4-3.7%)
MCP tool defs (configured)   ~???? tok (measure with mcp-governance)
─────────────────────────────────────────────
Fixed total (no opt docs)    ~2883 tok (1.10%)
Total w/ opt docs            ~13745 tok (5.24%)
Available for work           see `context_window` in `data/bundle-models.json`
```

**Note:** MODEL-GUIDE.md, TOOLS-MAP.md, and SKILL-TIERS.md are optional
reads (they do not load automatically). AGENTS.md is fixed.
