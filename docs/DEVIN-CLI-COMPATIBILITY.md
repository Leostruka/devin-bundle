# Devin CLI compatibility

## Validated release

The bundle is validated against Devin CLI `{{VALIDATED_CLI_VERSION}}` (see `data/bundle-identity.json`).

Release notes for the validated version and intermediate CLI versions are tracked in `data/bundle-identity.json` and the Devin CLI changelog.

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

Plugins remain in closed beta. The existing installer workflows remain the distribution mechanism until the official plugin interface leaves closed beta. No external MCP server is required or installed by compatibility tests.

The isolated fixture at `tests/fixtures/devin-plugin-prototype/.devin-plugin/plugin.json` contains no skills or MCP servers. It was accepted by `devin plugins install --local` under earlier validated CLI versions, and a first invocation without `--local` correctly refused to sync a local path to Devin Cloud; the local registration was removed after verification. The plugin interface has no changelog entries between documented releases, so the fixture remains valid under the current CLI.

## Installer verification

Run installers only against redirected temporary homes during automated compatibility checks. A valid simulation installs all skills and leaves the real user configuration untouched.

Windows uses a process-local temporary `APPDATA`. Unix uses a process-local temporary `XDG_CONFIG_HOME` or `HOME`, according to the installer contract.

## Primary sources

- Devin CLI stable changelog: https://docs.devin.ai/cli/changelog/stable
- Plugins: https://docs.devin.ai/cli/extensibility/plugins
- Lifecycle hooks: https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks
