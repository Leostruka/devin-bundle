# Devin CLI compatibility

## Validated release

The bundle is validated against Devin CLI `{{VALIDATED_CLI_VERSION}}` (see `data/bundle-identity.json`).

Release notes for the validated version and intermediate CLI versions are tracked in `data/bundle-identity.json` and the Devin CLI changelog.

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

`config.json` imports no foreign tool config (`cursor`, `windsurf`, `claude`, `copilot`, `opencode`, `zed` are all `false`): imported skills, hooks, and MCP servers from other agents are not part of the bundle's validated surface.

`agents_standard` is the exception: it gates only the standard rule files (`AGENTS.md`, `AGENTS.local.md`, `AGENT.md`, `.windsurfrules`), which are Devin CLI's native rules mechanism — the same mechanism the bundle's own `AGENTS.md` uses at the global level. Setting it `false` would silently disable every project-level `AGENTS.md` in repos the bundle is installed into, so the bundle ships `agents_standard: true`.

Primary verification commands:

```powershell
devin --version
devin models list
devin doctor
python audit.py
python -m pytest
```

## 3000.10.x capabilities (verified 2026-09-15, CLI 3000.10.27)

Decisions for configuration keys introduced between `3000.6.14` and `3000.10.27`:

| Capability | Decision | Rationale |
|---|---|---|
| `disabled_tools` | Not adopted | Bundle skills/scripts reference all relevant tools; disabling would remove documented capability without a measured gain. |
| `agent.compaction_threshold_tokens` | Not adopted | No evidence-backed non-default value; earlier compaction only increases constraint-drop events (pinning hook already covers them). |
| `PreToolUse` `tool_provenance` | Adopted passively | Field is additive in hook payloads; existing hook scripts ignore unknown keys. No config change needed. |
| `web_search` permission rules | Not adopted | `allow` adds nothing, `ask` adds friction, `deny` breaks research skills. |
| `/code`, `/smart`, `/bypass` modes | Adopted (docs) | Documented here; no config keys required. |
| Skill rediscovery after compaction | Adopted passively | CLI behavior; no bundle change. |
| `read_config_from.cursor` → `.cursor/skills/` | Not adopted | `cursor` stays `false`; bundle is Devin-native only (Rule: no platform leakage). |
| `agent.codex_tools` | Not adopted | Bundle uses SWE effort routing, not Codex tooling. |
| `shell.exec_shell` | Not adopted | Bundle hook commands are shell-agnostic `python` invocations. |
| `DEVIN_REFUSAL_FALLBACK` | Not adopted | Environment variable, not a config-template key. |
| GPT-6 Astra turn batching (3000.10.27) | Not applicable | Provider-side model behavior (fewer turns, targeted commands); no config surface. Bundle policy is SWE-2-only. |

## `read_config_from` policy

`config.json` sets `read_config_from.agents_standard: true` and every other foreign import to `false`. `agents_standard` is the Devin-native mechanism for project `AGENTS.md`/`AGENTS.local.md`/`AGENT.md`/`.windsurfrules` files — the same mechanism the bundle itself relies on for its global rules. Disabling it silently dropped project-level rules in every installed repository, contradicting the bundle's AGENTS-centric operating model. Other tool formats (`cursor`, `windsurf`, `claude`, `copilot`, `opencode`, `zed`) remain disabled: the bundle ships Devin-native skills/rules only, and importing foreign formats would be platform leakage.

## Model policy

`config.json` reads the primary model from `BUNDLE_DEFAULT_MODEL` (with `data/bundle-models.json` as the canonical registry). `devin models list` for the validated CLI reports the current free and paid models; the bundle's free-primary policy is enforced by choosing a `cost_tier: free` entry as the parent and matching subagent models from `data/bundle-models.json`.

The bundle default parent model is `{{BUNDLE_DEFAULT_MODEL}}` and the default subagent model is `{{BUNDLE_MAX_MODEL}}`, with `{{BUNDLE_MEDIUM_MODEL}}` as the lighter alternative. Short aliases that resolve to paid entries (see `data/bundle-models.json` aliases) are avoided.

Alternatives evaluated:

| Alternative | Result |
|---|---|
| Keep the CLI's default paid router | Valid model, but contradicts the bundle's explicit free-primary policy. |
| Pin `{{BUNDLE_DEFAULT_MODEL}}` | Matches the documented policy and the CLI model registry. Selected. |
| Omit the model | Delegates selection to local defaults and makes installs nondeterministic. |

Custom subagents remain pinned to `{{BUNDLE_MAX_MODEL}}` (see `data/bundle-models.json`). The `tools` frontmatter key is accepted as an alias for `allowed-tools` in recent CLI versions, but this bundle keeps `allowed-tools` as its canonical spelling.

## Lifecycle hooks

The global installer merges hooks from `config.json` into the user-level configuration. `hooks.v1.json` remains the project-level template.

The eight supported events are:

- `PreToolUse`: `tool_name`, `tool_input`.
- `PostToolUse`: `tool_name`, `tool_input`, `tool_response`.
- `PermissionRequest`: `tool_name`, `tool_input`.
- `UserPromptSubmit`: `prompt`.
- `Stop`: `stop_hook_active`, plus `last_assistant_message` in recent CLI versions.
- `PostCompaction`: `summary`.
- `SessionStart`: `source`.
- `SessionEnd`: `reason`.

Blocking `PreToolUse` hooks return exit code 2 and a top-level JSON decision containing `decision: block` and a reason. Since recent CLI releases, a blocked call reports its reason while the turn and sibling calls continue.

`memory-stop.py` accepts both `Stop` and `SessionEnd`; it consumes `SessionEnd.reason` without blocking. Stop handlers tolerate `last_assistant_message` without parsing transcripts.

## Plugins

Native plugins and Agent Plugins 1.0.0 are supported in recent CLI versions. Native plugin manifests use `.devin-plugin/plugin.json`; Agent Plugins use `plugin.json` at the plugin root.

The bundle ships `.devin-plugin/plugin.json`, so it can be installed as a native plugin:

```bash
devin plugins install --local .   # live-linked: edits apply next session
```

Plugin skills land under the `<plugin>:<skill>` namespace and install at user level. Two limits keep the installers (`install.ps1`/`install.sh`) as the primary path:

- **Plugin hooks are fail-open** (docs: "don't rely on them for crucial guardrails yet"). The bundle's hooks are guardrails, so they keep shipping via `hooks.v1.json` + rendered user config — deterministic, not best-effort.
- Plugins do not install `docs/`, `data/`, ledger conventions, or the `hooks.v1.json` project template — the installer covers the full surface.

The isolated fixture at `tests/fixtures/devin-plugin-prototype/.devin-plugin/plugin.json` contains no skills or MCP servers. It was accepted by `devin plugins install --local` under earlier validated CLI versions, and a first invocation without `--local` correctly refused to sync a local path to Devin Cloud; the local registration was removed after verification. The plugin interface has no changelog entries between documented releases, so the fixture remains valid under the current CLI.

## Sandbox and permissions

`devin --sandbox` (Research Preview) gives OS-level isolation for `exec` — writable roots, network filtering — and pairs with `--permission-mode autonomous`. It is the recommended way to run the bundle unattended on managed projects. Platform constraint: on Windows the sandbox requires Devin running inside WSL 2; sessions that pass `--sandbox` refuse to start outside WSL.

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
