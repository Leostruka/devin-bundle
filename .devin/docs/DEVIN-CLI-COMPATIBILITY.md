# Devin CLI compatibility

## Validated release

The bundle is validated against Devin CLI `3000.12.17` (see `data/bundle-identity.json`).

Release notes for the validated version and intermediate CLI versions are tracked in `data/bundle-identity.json` and the Devin CLI changelog.

## Verification cadence

This doc tracks `validated_cli_version` in `data/bundle-identity.json`.
Every section header is stamped with the CLI version it was checked
against (`verified <date>, CLI <version>`). Rule of maintenance: whenever
`validated_cli_version` advances, add a new `## <version> capabilities`
section covering every intermediate minor, and re-verify that each prior
adoption decision still holds. Owner: whoever bumps
`data/bundle-identity.json`; `audit.py` fails if the doc lags a validated
minor without a section.

## 3000.10.x capabilities (verified 2026-09-15, CLI 3000.10.27)

Capabilities added since 3000.6.x that interact with bundle surfaces, with the bundle's adoption decision:

| Capability | Decision | Rationale |
|---|---|---|
| GPT-6 Astra turn batching (3000.10.27) | not applicable | Provider-side model behavior (fewer turns, targeted commands); no config surface. Bundle policy is SWE-2-only. |
| `disabled_tools` (user `config.json`) | not adopted | Every tool in the surface is referenced by bundle skills/scripts (verified 2026-09-14: `notebook_*`, `browser_preview`, `write_to_process`, `kill_shell`, `get_output`, `ask_user_question`, `request_scope`, `mcp_*`, `read_subagent` all have refs). Disabling any would remove a documented capability. Revisit if a tool becomes provably unused. |
| `agent.compaction_threshold_tokens` (user config) | not adopted | No primary-source basis for a non-default value; the CLI default is context-window-based, and earlier compaction would only increase constraint-drop events that `constraint-pinning.py` must repair. |
| `PreToolUse` `tool_provenance` payload | adopted (passive) | Payload field, no config needed; hook scripts may consume it. Existing hook payloads remain compatible. |
| `web_search` in `permissions.allow/deny/ask` | not adopted | `allow` adds nothing (search was already auto-approved before 3000.10.x), `ask` adds friction, `deny` breaks research skills. |
| `/code`, `/smart`, `/bypass` mode commands | adopted (documented) | User-facing commands; nothing to configure. |
| Skills re-discovery after compaction; `.cursor/skills/` auto-load | adopted (passive) | CLI behavior; `.cursor/skills/` stays off because `read_config_from.cursor` ships `false`. |
| `agent.codex_tools` | not adopted | GPT-specific tool set; irrelevant under the SWE-2 model policy. |
| `shell.exec_shell` (beta) | not adopted | Bundle hook scripts are `python` invocations, shell-agnostic. |
| `DEVIN_REFUSAL_FALLBACK` env var | not adopted | Env var, not a `config.json` key; cannot be shipped via the config template. |

## `read_config_from` policy

`config.json` imports no foreign tool config (`cursor`, `windsurf`, `claude`, `copilot`, `opencode`, `zed` are all `false`): imported skills, hooks, and MCP servers from other agents are not part of the bundle's validated surface. Since `3000.11.228` `cloud` is also `false`: Devin Cloud MCP servers and personal plugins stay out of the CLI's validated surface; organization-required plugins still load per the CLI contract.

`agents_standard` is the exception: it gates only the standard rule files (`AGENTS.md`, `AGENTS.local.md`, `AGENT.md`, `.windsurfrules`), which are Devin CLI's native rules mechanism — the same mechanism the bundle's own `AGENTS.md` uses at the global level. Setting it `false` would silently disable every project-level `AGENTS.md` in repos the bundle is installed into, so the bundle ships `agents_standard: true`.

Since `3000.11.92`, a project's `.devin/config.json` `read_config_from` holds for everything loaded from that project even when the user config enables a provider, skills from a disabled provider can no longer be invoked by name or found by search, `devin rules list` honors `read_config_from`, and `.devin/global_rules.md` + `.devin/rules/` keep loading with `windsurf: false`.

Primary verification commands:

```powershell
devin --version
devin models list
devin doctor
python audit.py
python -m pytest
```

## 3000.11.x capabilities (verified 2026-09-22, CLI 3000.11.1)

Capabilities introduced in `3000.10.31` and `3000.11.1` that interact with bundle surfaces:

| Capability | Decision | Rationale |
|---|---|---|
| `Exec` deny beats broader `allow`/`ask`; `Exec(*)` matches all (3000.10.31) | adopted (passive) | Bundle ships only `Write`/`Read` deny rules for secrets; no `Exec` rules needed. `Exec(*)` is available if a future gate needs it. |
| Recursive rule discovery in `.devin/rules/` + `.windsurf/rules/` | adopted | Verified: `.devin/rules/README.md` listed as a `manual` rule (not always-on). README moved to `.devin/docs/` to keep `devin rules list` clean. |
| `allowed-tools` grants `write` in profiles/skills | adopted | Verified empirically: `implementer` subagent created a file; `researcher` has no write tool. Profiles already express intent — no change. |
| Subagents inherit global + workspace always-on rules | adopted (passive) | Verified: `researcher` quoted global AGENTS.md rule 2. Pinned constraints now reach subagents; small context cost per dispatch. |
| `devin --cloud`/`/cloud`, `/handoff`, `/pickup`, `devin ssh`/`/ssh` | adopted (docs) | New user-facing cloud commands; mapped in `TOOLS-MAP.md`. No config surface. |
| `otel` config block / `OTEL_EXPORTER_OTLP_*` | not adopted | No collector configured; `devin doctor` already validates the env. Revisit if an observability stack is adopted (`observability-quality`). |
| Org/enterprise plugins via Customize | documented | They now load in the CLI subject to the current org; bundle distribution stays on the installer. |
| `/loop` reviews in fresh read-only subagent | adopted (passive) | CLI behavior; no config. |
| Bypass mode skips editor review on file edits | documented | UX change only. |
| Interrupt parks running subagents | documented | Subagents survive interrupt (except Fusion sidekick); affects `afk-loop`/dispatch expectations. |
| PowerShell output/echo fixes; `devin forward` port release (Windows) | adopted (passive) | Upstream fixes; no bundle workarounds existed to remove. |
| ACP session config (model/effort/speed), auth cache | not adopted | Bundle does not run as an ACP server. |
| `AI_AGENT=devin_<version>_agent` in agent shells | adopted (passive) | Informational; hook scripts may key off it. |
| `/login` hidden in cloud sessions; session-lock identifies holder PID | documented | Minor UX/security hardening. |

## 3000.11.92 capabilities (verified 2026-10-15, CLI 3000.11.92)

Capabilities introduced in `3000.11.3` and `3000.11.92` that interact with bundle surfaces:

| Capability | Decision | Rationale |
|---|---|---|
| `agent.subagent_model` (user `config.json`) | adopted | Verified empirically: `subagent_explore` ran on SWE-2 Max with the key set vs SWE-2 High (parent inheritance) without it (`sessions.db` tool-result `subagent/model`). Ships `swe-2-max`, matching `default_subagent_model` in `data/bundle-models.json`. Affects `subagent_explore` and custom agents without a `model:` pin only; all bundle agent profiles pin explicitly. |
| `PreCompact`/`PostCompact` hook events (matchers `manual`/`auto`; failures non-blocking) | documented | Ten supported events now; existing `PostCompaction` remains supported and keeps `constraint-pinning.py`. Not adopted as a trigger: `compact-gate.py` decides when to compact, which a compaction notification cannot replace. Lifecycle-hooks docs page does not list them yet; changelog is the primary source. |
| `/goal <objective>` auto-continue (50-turn pause cap; `resume`/`clear`) | adopted (docs) | Runtime-native continuation across turns, overlapping `afk-loop` semantics at UI level; `afk-loop` stays the file-based DAG path. No config surface. |
| Steering: mid-work message feeds the running turn; `Ctrl+Enter` queues | documented | UX; no config. |
| Provider billing: `/billing on|off`, `Ctrl+S`, picker `*` for provider-plan models | documented | Provider plans can make paid models bill to the provider; the free-policy check remains `cost_tier` in `data/bundle-models.json`. |
| `Alt+Enter` session-only model pick; `model_picker.confirm_for_session` | documented | Session-scoped switch matters for the conditional model policy: parent switched to paid unlocks paid subagents for that session. |
| `typewriter` (streamed text without animation) | not adopted | Cosmetic; no basis to override the default. |
| `local_tools_bypass_permissions` | not adopted | Starts every `devin connect` in Bypass Permissions. `deny`/`ask` rules still apply, but the bundle's secure default is explicit approval; enable per-machine if wanted. |
| `DEVIN_SESSIONS_DIR` | not adopted | Env var, not a `config.json` key; same reasoning as `DEVIN_REFUSAL_FALLBACK`. |
| `plugins install owner/repo` accepts skills-only repos; `platforms` manifest field; `PLUGIN_ROOT`/`PLUGIN_DATA` for hooks; non-semver `version` loads | documented | Widens third-party skill/plugin sources (e.g. `anthropics/skills`). Distribution stays on the installer; hook fail-open posture unchanged. |
| MCP: protocol 2026-07-28, `Source:` line in `mcp list`/`get`, `User-Agent` header, remote MCPs via Devin Cloud (Private Preview, enterprise), OAuth eviction notice | adopted (passive) | Server/protocol side; `mcp_config.json` surface unchanged. `Source:` helps attribute servers to config files during `mcp-governance` audits. |
| OSC 7501 status reporting; `disable_osc` | not adopted | Terminal status reporting is harmless; no basis to silence it. |
| `sandbox.excluded.allow` (prompt option runs a command outside the sandbox); `Write(...)` allow auto-approves in autonomous mode | documented | Tightens the documented sandbox model; bundle sandbox guidance unchanged. |
| `devin connect` (hidden): image viewing + file copy local↔VM; rule-forced approvals name the rule | adopted (docs) | Verified present via `devin connect --help`; mapped in `TOOLS-MAP.md`. |
| `devin cloud` bare = cloud session; `cloud drs` subcommand | adopted (docs) | Verified in `--help`; `drs` manages Declarative Repo Setup blueprints/builds (companion to the `declarative-repo-setup` builtin skill). |
| Smart mode asks less; `--cloud` fast failure; proxy covers cloud WS + plugin downloads; NFS session DB fix; `--model` cold-start fix | adopted (passive) | Upstream reliability fixes; no bundle workarounds existed. |
| Rules fixes: `.devin/global_rules.md` + `.devin/rules/` load under `read_config_from.windsurf=false`; `rules list` honors `read_config_from`; always-on+glob rule injected once; mid-session rule dirs load | adopted (passive) | The bundle relies on exactly these paths; verified `devin rules list` clean (4 rules, no stray `manual`). |
| `read_config_from` in project `.devin/config.json` fully honored; disabled-provider skills blocked from invoke/search | adopted (passive) | Strengthens the bundle's `read_config_from` policy below. |
| Hook fixes: foreign `Notification`/`SubagentStop` events no longer disable the whole hooks file; Windsurf-format hooks fire on GPT models | adopted (passive) | Bundle hooks use the native format; resilience improvement only. |
| `/context` token table; `/normal` = `/code` alias in ACP; `/bug` failure reasons; session search by relevance; `/usage` live refresh; `Ctrl+U`/`Ctrl+C` draft handling; force-open held sessions; per-message effort keeps prompt cache | documented | UX/ACP fixes; no config. |
| `3000.11.3`: dedicated-tenant login host recorded for `/handoff`/`/share` links | adopted (passive) | Login fix; re-run `/login` to pick it up on affected tenants. |

## 3000.11.228 capabilities (verified 2026-10-27, CLI 3000.11.228)

Capabilities introduced in `3000.11.205` and `3000.11.228` that interact with bundle surfaces:

| Capability | Decision | Rationale |
|---|---|---|
| `fail_closed: true` hook field | adopted | Verified empirically on a scratch project: a `PreToolUse` hook exiting 1 logged "Hook failed" and let `exec` run without the flag, and answered "Blocked: a required PreToolUse hook failed" with `fail_closed: true`. Ships on both guard matchers (`pre-exec-guard.py`, `pre-write-guard.py`) so a broken gate blocks the action instead of passing it. Observer hooks (PostToolUse, prompt, lifecycle) stay fail-open by design. |
| `read_config_from.cloud` | adopted | Ships `false`: keeps Devin Cloud MCP servers and personal plugins out of the CLI, matching the `read_config_from` policy above. Organization-required plugins still load per the CLI contract. |
| Hook output `stop: "<reason>"` (any event; Claude-format `continue: false`/`stopReason` also read) | documented | New turn-end channel from any event. `stop-guard.py` still blocks via `decision`; no bundle script switched yet. |
| `PostToolUse` `hookSpecificOutput.updatedToolOutput` | documented | Rewrites the tool result before the model reads it (redaction use case). Reserved; no current consumer in the bundle. |
| `/loop` + `agent.model_mixture` removed | noted | Replaced by `/goal`. The bundle never adopted `model_mixture`, and `scheduled-turns` runs `devin -p` one-shots, so no bundle change needed. |
| `DEVIN_SESSION_STORE=files` (experimental) | not adopted | Env var that keeps session history as files on NFS/SMB homes; same reasoning as `DEVIN_SESSIONS_DIR` (env, not a `config.json` key). |
| `agent.verbosity` | adopted = `3` | Integer 0-3 (default 1 = compact single-line tool summaries introduced in 3000.11.205); `3` restores full tool cards/diffs in the transcript. |
| Permission UX: prompt shows the exact rule (`Exec(docker build)`), Allow/Bypass/Deny with grant duration (`Once`/`Session`/`Project`/`Always`) and `e` to edit the command | adopted (passive) | Approval cards now name the matched bundle rule (`Write(**/.env*)` denies etc.). No config surface. |
| `/rename` (no-arg auto-title), `/pickup` cloud summary, `/confetti`, `devin models` listing | adopted (docs) | Mapped in `TOOLS-MAP.md`. |
| Compact tool calls with `Ctrl+O` expansion, `/config` editor redesign, `/context` per-section bars, `/model` Desktop ordering, instant session picker with title search, `/resume` picker over the running session | documented | UX changes; no config. |
| Steering interrupts immediately while preserving long-running command progress | adopted (passive) | Improves the mid-work message path shipped in `3000.11.92`. |
| Session privacy on `devin --cloud`/Desktop connect; `local_exec` credential-path approval without `~`; hook matcher list-of-strings; MCP `server/discover` tolerance; interrupt during MCP connect | adopted (passive) | Security/reliability fixes aligned with the bundle's threat model. |
| `3000.11.228`: session DB partial-migration repair on startup; inline-image (sixel/iTerm2/kitty) crash fix | adopted (passive) | Upstream reliability fixes; no bundle workarounds existed. |

## 3000.11.234 capabilities (verified 2026-10-30, CLI 3000.11.234)

Capabilities and runtime contracts verified in `3000.11.234` (`92c83011d113`) since `3000.11.228`:

| Capability | Decision | Rationale |
|---|---|---|
| `--verbosity <0..3>` CLI flag / `DEVIN_VERBOSITY` env var | documented | Per-run override for `agent.verbosity` (`0` quiet, `1` compact, `2` detailed, `3` verbose). Bundle `config.json` keeps `"verbosity": 3` as the persistent default. |
| Hook stdin correlation IDs (`session_id`, `prompt_id`) | adopted (passive) | Every hook stdin payload carries a session-wide `session_id` and a per-turn `prompt_id` (rotated on each `UserPromptSubmit`; absent before the first user prompt, e.g. `SessionStart`). Available for `_hookrun.py`, ledger correlation, and per-turn caching without extra state files. |
| `PreToolUse` `hookSpecificOutput.updatedInput` | documented | Merges rewritten arguments into `tool_input` before tool execution (e.g. wrapping `exec` commands). Bundle guards currently block or allow without mutating arguments; reserved for transparent command wrappers. |
| `keymap` strict `-`-separated key-spec validation at startup | adopted | Modifiers use `-` (`ctrl-4`, `ctrl-shift-k`); unknown contexts/actions, malformed specs, or intra-context collisions emit startup warnings and fall back to built-in defaults (`global.cancel` `Ctrl+C` cannot be unbound). Aligned in `config.json` (`"queue_message": "ctrl-4"`). |
| `devin desktop [ARGS]...` subcommand and positional `[PATH]...` | adopted (docs) | Launches Devin Desktop matching the CLI channel and forwards path arguments. Mapped in `TOOLS-MAP.md`. |
| `devin acp --agent-type <summarizer\|review>` and `--refusal-fallback <MODEL>` | not adopted | ACP-specific flags (`DEVIN_REFUSAL_FALLBACK` env var remains outside `config.json`). |

## 3000.12.17 capabilities (verified 2026-11-07, CLI 3000.12.17)

Capabilities and runtime contracts verified in `3000.12.17` (`d23bb600ed8f`) since `3000.11.234`:

| Capability | Decision | Rationale |
|---|---|---|
| `/vim` Vim editing in the prompt box (Esc -> Normal mode) | adopted (docs) | UX; no config surface. |
| Model pinning: `Alt+P` in `/model`, `Alt+N` cycles pins | adopted (docs) | Complements the bundle model policy: pin the free `swe-2-*` entries per machine so they surface first in the picker. |
| `permission_mode` settable via `/config`; `--permission-mode` overrides per launch | documented | New persistent config key for the starting permission mode. Bundle `config.json` does not ship it: the CLI default (`auto`) stays the validated surface; pin per-machine via `/config` if wanted. |
| `devin mcp list --json` | adopted (docs) | Machine-readable MCP inventory (enabled state, transport, disabled tools); verified locally (returns `[]` with no servers). Useful for `mcp-governance` audits. |
| Clipboard images: `Alt+V` on Windows, `Ctrl+V`/`Alt+V` in WSL | adopted (docs) | UX; no config. |
| `/resume` shows project + age; `Alt+G` toggles current-dir vs all-projects | documented | UX; no config. |
| Approval prompt `1`/`2`/`3`/`4` = Once/Session/Project/Always | adopted (passive) | Keyboard equivalent of the arrow-key grant picker shipped in 3000.11.205. |
| `/clear` type-ahead prompt queue | documented | UX; no config. |
| `ContextInput` hooks observe relayed text (e.g. subagent reports) | documented | New hook surface per changelog; not yet listed on the lifecycle-hooks docs page. No bundle consumer wired yet. |
| `PostToolUse` hooks receive path to complete output when result is truncated | documented | New payload field per changelog. Candidate for `post-exec.py`/`silent-error-review` to read full output instead of the truncated inline copy; no consumer switched yet. |
| `UserPromptSubmit` hooks run on `/handoff` task transfer | adopted (passive) | Closes a constraint-drop channel: `constraint-pinning.py` now re-injects pinned constraints when a task moves to a cloud session. |
| `/config` changes apply on `/clear`, `/resume`, `/cloud` without restart | adopted (passive) | Reliability fix. |
| Fixes: plan-approval summary+path, follow-up during pending edit approval, Accept Edits/Smart on Windows network shares + WSL folders, rapid config-save loss, undecodable images no longer fail the turn, `devin -p` continues after denied tool call, log-file failure warns instead of breaking, PowerShell non-ASCII output | adopted (passive) | Upstream fixes; several hit Windows/WSL paths the bundle supports. No workarounds existed to remove. |

## 3000.12.28 capabilities (verified 2026-11-08, CLI 3000.12.28)

Capabilities and runtime contracts verified in `3000.12.28` (`91c3aec41579`) since `3000.12.17`. The public stable changelog tops out at `3000.12.17`; the delta was probed directly on the installed binary.

| Capability | Decision | Rationale |
|---|---|---|
| `devin sandbox` subcommand (`sandbox setup` prints platform prerequisites) | documented | Sandboxing is now a subcommand alongside the `--sandbox` flag/`DEVIN_SANDBOX` env. On Windows it still refuses outside WSL 2 - the constraint the compat doc already records stands. |
| `--respect-workspace-trust [true|false]` | documented | New launch flag: non-interactive (`-p`) mode cannot show the trust prompt and fails in untrusted directories unless `false` is passed; `--cloud` never checks trust. Relevant for scripted `devin -p` invocations in fresh dirs. |
| `devin doctor` passes 3/3 against the live bundle | adopted (passive) | Verified post-upgrade: custom subagent profiles (26), OTEL env, OTEL export. |
| `devin update` on Windows prints manual `irm ... install.ps1` instruction | documented | No in-binary self-update on Windows; the manifest at `static.devin.ai/cli/current/manifest.json` confirmed `3000.12.28` is the latest promoted build. |

## Model policy

`config.json` reads the primary model from `BUNDLE_DEFAULT_MODEL` (with `data/bundle-models.json` as the canonical registry). `devin models list` for the validated CLI reports the current free and paid models; the bundle's free-primary policy is enforced by choosing a `cost_tier: free` entry as the parent and matching subagent models from `data/bundle-models.json`.

The bundle default parent model is `swe-2-high` and the default subagent model is `swe-2-max`, with `swe-2-medium` as the lighter alternative. Short aliases that resolve to paid entries (see `data/bundle-models.json` aliases) are avoided.

Alternatives evaluated:

| Alternative | Result |
|---|---|
| Keep the CLI's default paid router | Valid model, but contradicts the bundle's explicit free-primary policy. |
| Pin `swe-2-high` | Matches the documented policy and the CLI model registry. Selected. |
| Omit the model | Delegates selection to local defaults and makes installs nondeterministic. |

Custom subagents remain pinned to `swe-2-max` (see `data/bundle-models.json`). Since `3000.11.92`, `agent.subagent_model` in `config.json` pins the fallback model for `subagent_explore` and any custom agent without its own `model:`; the template ships `swe-2-max`, matching `default_subagent_model`. The `tools` frontmatter key is accepted as an alias for `allowed-tools` in recent CLI versions, but this bundle keeps `allowed-tools` as its canonical spelling.

## Lifecycle hooks

The global installer merges hooks from `config.json` into the user-level configuration. `hooks.v1.json` remains the project-level template.

The ten supported events are:

- `PreToolUse`: `tool_name`, `tool_input`.
- `PostToolUse`: `tool_name`, `tool_input`, `tool_response`.
- `PermissionRequest`: `tool_name`, `tool_input`.
- `UserPromptSubmit`: `prompt`.
- `Stop`: `stop_hook_active`, plus `last_assistant_message` in recent CLI versions.
- `PostCompaction`: `summary`.
- `SessionStart`: `source`.
- `SessionEnd`: `reason`.
- `PreCompact` (since 3000.11.92): fires before compaction; `manual`/`auto` trigger matchers; failures do not block compaction. Not yet on the lifecycle-hooks docs page.
- `PostCompact` (since 3000.11.92): fires after compaction; same matchers and non-blocking semantics. Distinct from `PostCompaction`, which remains supported.

Blocking `PreToolUse` hooks return exit code 2 and a top-level JSON decision containing `decision: block` and a reason. Since recent CLI releases, a blocked call reports its reason while the turn and sibling calls continue.

Since `3000.11.205`, a hook entry can set `fail_closed: true` to block the guarded action when the hook itself fails to run; the bundle ships it on the two `PreToolUse` guard matchers only (verified empirically). `stop: "<reason>"` in hook output ends the turn from any event, `PreToolUse` `hookSpecificOutput.updatedInput` merges rewritten arguments before execution, and `PostToolUse` `hookSpecificOutput.updatedToolOutput` rewrites the tool result before the model reads it. Every hook stdin payload also includes `session_id` (session-stable) and `prompt_id` (rotated per user prompt; absent on `SessionStart`).

`memory-stop.py` accepts both `Stop` and `SessionEnd`; it consumes `SessionEnd.reason` without blocking. Stop handlers tolerate `last_assistant_message` without parsing transcripts.

## Plugins

Native plugins and Agent Plugins 1.0.0 are supported in recent CLI versions. Native plugin manifests use `.devin-plugin/plugin.json`; Agent Plugins use `plugin.json` at the plugin root.

Since `3000.11.1`, optional organization and enterprise plugins installed through Customize also load in the CLI (subject to the current organization). Since `3000.11.92`: `plugins install owner/repo` accepts skills-only repos without a plugin manifest; plugin manifests can scope to `platforms` (`cloud`/`local`); plugin hooks resolve `PLUGIN_ROOT` and `PLUGIN_DATA` (data surviving updates); non-semver `version` strings load instead of being rejected. This does not change the bundle's distribution path.

The bundle does **not** ship as a plugin — `install.ps1`/`install.sh` remain the distribution path, for two reasons:

- **Plugin hooks are fail-open** (docs: "don't rely on them for crucial guardrails yet"). The bundle's hooks are guardrails, so they keep shipping via `hooks.v1.json` + rendered user config — deterministic, not best-effort.
- Plugins do not install `docs/`, `data/`, ledger conventions, or the `hooks.v1.json` project template — the installer covers the full surface.

The isolated fixture at `tests/fixtures/devin-plugin-prototype/.devin-plugin/plugin.json` contains no skills or MCP servers. It was accepted by `devin plugins install --local` under earlier validated CLI versions, and a first invocation without `--local` correctly refused to sync a local path to Devin Cloud; the local registration was removed after verification. The plugin interface has no changelog entries between documented releases, so the fixture remains valid under the current CLI.

## Sandbox and permissions

`devin --sandbox` (Research Preview) gives OS-level isolation for `exec` — writable roots, network filtering — and pairs with `--permission-mode autonomous`. It is the recommended way to run the bundle unattended on managed projects. Platform constraint: on Windows the sandbox requires Devin running inside WSL 2; sessions that pass `--sandbox` refuse to start outside WSL.

Since `3000.11.92`, sandbox permission prompts can offer `sandbox.excluded.allow` (run a command outside the sandbox permanently), and `Write(...)` allow rules auto-approve matching file edits in autonomous mode.

The user-level `config.json` template ships native deny rules that cover the destructive-gate's secret-file cases at CLI level (a deny rule always wins, no prompt):

```json
"permissions": {
  "deny": ["Write(**/.env*)", "Write(**/credentials*)", "Read(**/.env*)"]
}
```

Command-pattern analysis (`rm -rf`, force-push, pipe-to-shell) stays in the Python destructive gate — `permissions` rules match tool/path scopes, not command content.

## Installer verification

Run installers only against redirected temporary homes during automated compatibility checks. A valid simulation installs all skills and leaves the real user configuration untouched.

Windows uses a process-local temporary `APPDATA`. Unix uses a process-local temporary `XDG_CONFIG_HOME` or `HOME`, according to the installer contract.

## Primary sources

- Devin CLI stable changelog: https://docs.devin.ai/cli/changelog/stable
- Plugins: https://docs.devin.ai/cli/extensibility/plugins
- Lifecycle hooks: https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks
